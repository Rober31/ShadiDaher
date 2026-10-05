"""Render the ZEIAD film from edl.py.

  python3 render.py --clips clips/ --out out/zeiad_50s.mp4

clips/<ID>.mp4 for video sources, clips/<ID>.png for stills (mode 'still').
Per shot: exact frame range [round(t0*fps), round(t1*fps)) -> lossless intermediate,
then concat, unified grade, and the final mix from mix.py.
"""
import argparse, importlib.util, json, os, subprocess, sys

W, H = 1080, 1920
NAVY = '0x02060D'

GRADES = {
    # cool navy shadows, warm metal kept natural; no orange-teal push
    'modern':  "eq=contrast=1.04:saturation=0.97:gamma=0.98,"
               "colorbalance=rs=-0.02:bs=0.03:rm=0.00:bm=0.00:rh=0.01:bh=-0.01",
    'vintage': "eq=contrast=1.02:saturation=0.98:gamma=1.0,"
               "colorbalance=rs=-0.01:bs=0.025:rm=0.02:gm=0.01:bm=-0.015:rh=0.015:bh=-0.015,"
               "colortemperature=temperature=6100:mix=0.35",
    'neutral': "eq=contrast=1.03:saturation=0.98,colorbalance=bs=0.025:rs=-0.015",
}
# shared finishing: navy-black floor (#02060D), soft vignette, fine grain to glue AI sources
FINISH = ("curves=r='0/0.008 1/1':g='0/0.024 1/1':b='0/0.051 1/0.995',"
          "vignette=angle=PI/5.5:mode=forward,"
          "noise=c0s=3:c0f=t+u:c1s=1:c1f=t+u:c2s=1:c2f=t+u")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(' '.join(cmd)); print(r.stderr[-3000:]); sys.exit(1)
    return r


def probe(path):
    r = run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
             'stream=width,height,r_frame_rate,nb_frames:format=duration', '-of', 'json', path])
    j = json.loads(r.stdout); s = j['streams'][0]
    n, d = s['r_frame_rate'].split('/')
    return dict(w=s['width'], h=s['height'], fps=float(n) / float(d), dur=float(j['format']['duration']))


def fit(z=1.0):
    """scale to cover 1080x1920 (with optional static punch-in), centre crop."""
    return (f"scale={W}*{z}:{H}*{z}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H}")


def shot_filter(sh, fps, nframes, src_info):
    D = nframes / fps
    mode = sh['mode']
    f = []
    if mode == 'play':
        sp = sh.get('speed', 1.0)
        f += [f"trim=start={sh['src_in']}:duration={D * sp + 0.5}", "setpts=PTS-STARTPTS"]
        if sp != 1.0:
            f += [f"setpts=PTS/{sp}"]
    elif mode == 'reverse':
        L = sh['src_out'] - sh['src_in']
        f += [f"trim=start={sh['src_in']}:end={sh['src_out']}", "setpts=PTS-STARTPTS", "reverse",
              f"setpts=PTS*{D / L}"]
    elif mode in ('ramp_in', 'ramp_out'):
        L = sh['src_out'] - sh['src_in']
        f += [f"trim=start={sh['src_in']}:end={sh['src_out']}", "setpts=PTS-STARTPTS"]
        if sh.get('reverse'):
            f += ["reverse"]
        f += ["tmix=frames=3:weights='1 2 1'"]
        if mode == 'ramp_in':      # accelerating: t = D*sqrt(T/L)
            f += [f"setpts='({D})*sqrt(min(T/{L},1))/TB'"]
        else:                      # decelerating: t = D*(1-sqrt(1-T/L))
            f += [f"setpts='({D})*(1-sqrt(max(1-T/{L},0)))/TB'"]
    elif mode == 'freeze_tail':
        f += [f"trim=start={sh['src_in']}", "setpts=PTS-STARTPTS",
              f"tpad=stop_mode=clone:stop_duration={D + 1}"]
    elif mode == 'still':
        pass  # handled separately
    f += [f"fps={fps}", fit(sh.get('zoom', 1.0))]
    if 'push' in sh:               # slow digital push-in over the shot
        z0, z1 = sh['push']
        f += [f"scale=w='trunc({W}*({z0}+({z1}-{z0})*t/{D})/2)*2':h='trunc({H}*({z0}+({z1}-{z0})*t/{D})/2)*2'"
              f":eval=frame:flags=lanczos", f"crop={W}:{H}"]
    if sh.get('settle'):           # final hero: imperceptible push so the held frame still breathes
        f += [f"scale=w='trunc({W}*(1+0.012*t/{D})/2)*2':h='trunc({H}*(1+0.012*t/{D})/2)*2'"
              f":eval=frame:flags=lanczos", f"crop={W}:{H}"]
    f += [GRADES[sh.get('grade', 'neutral')]]
    if sh.get('fade_out_to_navy'):
        d = sh['fade_out_to_navy']
        f += [f"fade=t=out:st={D - d}:d={d}:color={NAVY}"]
    if sh.get('fade_in_from_navy'):
        f += [f"fade=t=in:st=0:d={sh['fade_in_from_navy']}:color={NAVY}"]
    # clone-pad so every shot has exactly nframes even when retiming lands a frame short
    f += ["tpad=stop_mode=clone:stop_duration=0.5", f"trim=end_frame={nframes}", "setpts=PTS-STARTPTS",
          "format=yuv444p"]
    return ','.join(f)


def render_shot(i, sh, fps, clips, tmp):
    f0, f1 = round(sh['t0'] * fps), round(sh['t1'] * fps)
    n = f1 - f0
    out = os.path.join(tmp, f"s{i:02d}.mov")
    enc = ['-c:v', 'prores_ks', '-profile:v', '4', '-pix_fmt', 'yuv444p10le', '-an', out]
    if sh['mode'] == 'navy':
        run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i',
             f"color=c={NAVY}:s={W}x{H}:r={fps}:d={n / fps + 0.2},noise=c0s=3:c0f=t+u,"
             f"trim=end_frame={n},format=yuv444p", *enc])
        return out, n
    if sh['mode'] == 'segments':
        # piecewise retime of one source: [(s_from, s_to, out_seconds, ease, blur_frames)], s_to < s_from plays backward
        src = os.path.join(clips, sh['src'] + '.mp4')
        chains, labels, acc_f = [], [], 0
        for k, (sa, sb, d, ease, blur) in enumerate(sh['segs']):
            lo, hi = min(sa, sb), max(sa, sb); L = hi - lo
            kf = n - acc_f if k == len(sh['segs']) - 1 else round(d * fps)
            acc_f += kf; D = kf / fps
            c = [f"trim=start={lo}:end={hi}", "setpts=PTS-STARTPTS"]
            if sb < sa:
                c += ["reverse"]
            if blur > 1:
                c += [f"tmix=frames={blur}"]
            if ease == 'out':
                c += [f"setpts='({D})*(1-sqrt(max(1-T/{L},0)))/TB'"]
            elif ease == 'in':
                c += [f"setpts='({D})*sqrt(min(T/{L},1))/TB'"]
            else:
                c += [f"setpts=PTS*{D / L}"]
            c += [f"fps={fps}", "tpad=stop_mode=clone:stop_duration=0.5", f"trim=end_frame={kf}", "setpts=PTS-STARTPTS"]
            chains.append(f"[0:v]{','.join(c)}[g{k}]"); labels.append(f"[g{k}]")
        post = [fit(sh.get('zoom', 1.0)), GRADES[sh.get('grade', 'neutral')]]
        if sh.get('fade_in_from_navy'):
            post += [f"fade=t=in:st=0:d={sh['fade_in_from_navy']}:color={NAVY}"]
        post += [f"trim=end_frame={n}", "format=yuv444p"]
        fc = ';'.join(chains) + ';' + ''.join(labels) + f"concat=n={len(labels)}:v=1:a=0,{','.join(post)}[v]"
        run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-filter_complex', fc, '-map', '[v]', *enc])
        return out, n
    if sh['mode'] == 'stills_seq':
        # a sequence of stills that cut on exact frames under ONE continuous digital push
        D = n / fps
        z0, z1 = sh.get('z0', 1.0), sh.get('z1', 1.1)
        ins, chains, labels, acc = [], [], [], 0
        for k, (img, dur) in enumerate(sh['seq']):
            k0 = round(acc * fps); acc += dur
            k1 = n if k == len(sh['seq']) - 1 else round(acc * fps)
            ins += ['-loop', '1', '-t', f"{D + 0.5}", '-i', os.path.join(clips, img + '.png')]
            chains.append(
                f"[{k}:v]fps={fps},scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={W * 2}:{H * 2},setsar=1,trim=start_frame={k0}:end_frame={k1}[p{k}]")
            labels.append(f"[p{k}]")
        fc = ';'.join(chains) + ';' + ''.join(labels) + f"concat=n={len(labels)}:v=1:a=0,setpts=N/({fps}*TB)," \
             f"scale=w='trunc({W * 2}*({z0}+({z1}-{z0})*t/{D})/2)*2':h='trunc({H * 2}*({z0}+({z1}-{z0})*t/{D})/2)*2'" \
             f":eval=frame:flags=lanczos,crop={W * 2}:{H * 2},scale={W}:{H}:flags=lanczos," \
             f"{GRADES[sh.get('grade', 'neutral')]},trim=end_frame={n},format=yuv444p[v]"
        run(['ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', fc, '-map', '[v]', *enc])
        return out, n
    if sh['mode'] == 'still':
        D = n / fps
        z0, z1 = sh.get('z0', 1.0), sh.get('z1', 1.02)
        img = os.path.join(clips, sh['src'] + '.png')
        vf = (f"fps={fps},scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W * 2}:{H * 2},"
              f"scale=w='trunc({W * 2}*({z0}+({z1}-{z0})*t/{D})/2)*2':h='trunc({H * 2}*({z0}+({z1}-{z0})*t/{D})/2)*2'"
              f":eval=frame:flags=lanczos,crop={W * 2}:{H * 2},scale={W}:{H}:flags=lanczos,"
              f"{GRADES[sh.get('grade', 'neutral')]},trim=end_frame={n},format=yuv444p")
        run(['ffmpeg', '-y', '-v', 'error', '-loop', '1', '-t', f"{D + 0.5}", '-i', img, '-vf', vf, *enc])
        return out, n
    src = os.path.join(clips, sh['src'] + '.mp4')
    info = probe(src)
    vf = shot_filter(sh, fps, n, info)
    run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vf', vf, '-r', str(fps), *enc])
    return out, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clips', default='clips')
    ap.add_argument('--edl', default='edl.py')
    ap.add_argument('--audio', default='mix_final.wav')
    ap.add_argument('--out', default='out/zeiad_50s.mp4')
    ap.add_argument('--fps', type=float, default=24.0)
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location('edl', a.edl)
    edl = importlib.util.module_from_spec(spec); spec.loader.exec_module(edl)
    tmp = 'build'; os.makedirs(tmp, exist_ok=True); os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    parts, total = [], 0
    only = {int(x) for x in a.only.split(',') if x}
    for i, sh in enumerate(edl.SHOTS):
        if only and i not in only:
            parts.append(os.path.join(tmp, f"s{i:02d}.mov")); continue
        p, n = render_shot(i, sh, a.fps, a.clips, tmp)
        parts.append(p); total += n
        print(f"shot {i:02d} {sh['t0']:6.2f}-{sh['t1']:6.2f} {sh['mode']:11s} {sh.get('src')} frames={n}")
    with open(os.path.join(tmp, 'concat.txt'), 'w') as fh:
        for p in parts:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    master = os.path.join(tmp, 'master.mov')
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(tmp, 'concat.txt'),
         '-vf', FINISH, '-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', master])
    run(['ffmpeg', '-y', '-v', 'error', '-i', master, '-i', a.audio,
         '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
         '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
         '-color_trc', 'bt709', '-x264-params', 'keyint=48:min-keyint=24',
         '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest', '-movflags', '+faststart', a.out])
    print('wrote', a.out)


if __name__ == '__main__':
    main()
