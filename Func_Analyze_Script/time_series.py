import numpy as np
import argparse

def time_series_generate(
    runs:int,
    TR:float,
    total_duration:float,
    mode:str,
    time_spacing:float,
    filename:str
):

    times = []
    start = 0

    All_bricks = total_duration / TR
    Epoch_bricks = All_bricks / runs
    bricks = Epoch_bricks
    
    print(f"[DEBUG-python]: bricks={bricks}")

    for i in range(runs):
        print(f"[DEBUG-python]: start={start} | stop={start+bricks*TR}")
        #if mode == "Event":
        #    excitation = np.arange(start=start, step=bricks*TR, stop=start+bricks*TR).astype(np.float16)
        #elif mode == "Block":
            # excitation = np.arange(start=start, step=TR, stop=start+bricks*TR).astype(np.float16)
            
        #else:
        #    raise ValueError(f"[Error-python]: <time-series-generate> only suppport two experiment's modes: [Block] or [Event] ...")

        #t = [str(j) for j in excitation]

        #times.append(" ".join(t))

        #start = float(t[-1])

        #if time_spacing:
        #    start += time_spacing
        #start += TR
        
        if i % 2 == 1:
            if mode in ["Block", "Event"]:
                times.append("0")
        else:
            times.append("*")

    file_content = "\n".join(times)

    with open(filename, mode="w+", encoding='utf-8') as F:
        F.write(file_content)
        F.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Params Explanation of Time-series Generator ...")

    parser.add_argument('--runs', '-R', dest='runs', required=True, help="How many run times in your fMRI data?")

    parser.add_argument('--time_repetation', '-TR', dest='tr', required=True, help="How long time repetation(TR) in you fMRI data attribution?")

    parser.add_argument('--duration', '-D', dest='td', required=True, help="The total experiment duration")

    parser.add_argument('--time_spacing', '-TS', dest='ts', required=False, default=0., help="If the experiment duration is not continuous, please assign the time spacing ...")

    parser.add_argument('--mode', '-M', dest='mode', required=False, default='Block', help="Which mode is taken for your experimental data acquistion? Default is [Block]" )

    parser.add_argument('--output', '-O', dest='output', required=True, help="The output filename")

    args = parser.parse_args()

    runs = int(args.runs)
    tr = float(args.tr)
    duration = float(args.td)
    ts = float(args.ts)
    mode = args.mode
    out_file = args.output

    print(
        f"[Info-python]: Execute <Time Series Generate> ..."+"\n",
        f"===> Runs:{runs} | TR:{tr} | Duration:{duration}"+"\n",
        f"===> Time spacing:{ts}" +"\n",
        f"===> Mode:{mode} | Output Filename:{out_file}"
    )


    time_series_generate(runs, tr, duration, mode, ts, out_file)


