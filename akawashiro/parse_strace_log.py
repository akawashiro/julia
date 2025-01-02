import argparse
from dataclasses import dataclass
import os
import logging
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)


@dataclass
class Process:
    pid: int
    start_time: int
    end_time: int
    program: str


def plot_processes(processes: list[Process], image_file: str) -> None:
    LIMIT_SHORTEST_PROCESS_SEC = 10
    processes = list(filter(lambda p: p.end_time > p.start_time + LIMIT_SHORTEST_PROCESS_SEC, processes))
    processes.sort(key=lambda p: p.start_time)

    offset_time = 1 << 32
    max_time = 0
    for p in processes:
        s = p.start_time
        e = p.end_time
        offset_time = min(offset_time, s)
        max_time = max(max_time, e)
    logging.info(
        f"offset_time: {offset_time}, max_time: {max_time}, duration: {max_time - offset_time}"
    )

    vcpu_used_times: list[int] = [0] * len(processes)
    process_to_vcpu: list[int] = [-1] * len(processes)
    for i, p in enumerate(processes):
        for j in range(len(vcpu_used_times)):
            if vcpu_used_times[j] <= p.start_time:
                vcpu_used_times[j] = p.end_time
                process_to_vcpu[i] = j
                break
    max_vcpu = max(process_to_vcpu) + 1
    logging.info(f"max_vcpu: {max_vcpu}")

    fig, ax = plt.subplots(dpi=100, figsize=(128, 6))
    ax.set_xlim(0, max_time - offset_time)
    ax.set_xlabel("Time (sec)")
    ax.set_xticks(range(0, max_time - offset_time, 100))
    ax.set_ylim(0, max_vcpu)
    ax.set_yticks([])

    for i, p in enumerate(processes):
        s = p.start_time - offset_time
        e = p.end_time - offset_time
        v = process_to_vcpu[i]
        logging.info(f"{p.program} {s} {e} {v}")

        r = patches.Rectangle(
            (s, v),
            e - s,
            1.0,
            facecolor="none",
            edgecolor="black",
        )
        ax.add_patch(r)

        rx, ry = r.get_xy()
        cx = rx + r.get_width() / 2.0
        cy = ry + r.get_height() / 2.0
        text = os.path.basename(p.program)
        ax.annotate(
            text,
            (cx, cy),
            color="black",
            weight="bold",
            fontsize=6,
            ha="center",
            va="center",
        )

    
    fig.suptitle(f"Processes shorted than {LIMIT_SHORTEST_PROCESS_SEC} sec are omitted")
    fig.savefig(image_file)


def generate_trace_json(processes: list[Process]) -> str:
    processes = list(filter(lambda p: p.end_time > p.start_time, processes))

    trace = []
    offset_time = 1 << 32

    dummy_pids: dict[str, int] = {}

    for p in processes:
        s = p.start_time * 1000
        e = p.end_time * 1000
        if p.program not in dummy_pids:
            dummy_pids[p.program] = len(dummy_pids)
        dummy_pid = dummy_pids[p.program]

        offset_time = min(offset_time, s)
        trace.append(
            {
                "name": p.program,
                "cat": p.program,
                "ts": s,
                "ph": "B",
                "pid": dummy_pid,
                "tid": p.pid,
                "args": {},
            }
        )
        trace.append(
            {
                "name": p.program,
                "cat": p.program,
                "ph": "E",
                "ts": e,
                "pid": dummy_pid,
                "tid": p.pid,
                "args": {},
            }
        )
    for t in trace:
        t["ts"] -= offset_time
    trace_json = {
        "traceEvents": trace,
        "displayTimeUnit": "ms",
    }
    return json.dumps(trace_json, indent=4)


def main(log_file: str, output_json: str, output_image: str) -> None:
    # pid -> Process
    processes: dict[int, Process] = {}
    with open(log_file, "r") as f:
        for line in f:
            line = line.replace("(", " ").replace('"', " ")
            ws = line.split()
            if len(ws) > 2 and ws[2] == "execve":
                p = Process(
                    pid=int(ws[0]),
                    start_time=int(ws[1]),
                    end_time=(1 << 32),
                    program=ws[3],
                )
                processes[p.pid] = p
            if len(ws) > 2 and ws[2] == "exit" or ws[2] == "exit_group":
                if int(ws[0]) in processes:
                    processes[int(ws[0])].end_time = int(ws[1])
                else:
                    logging.warning(f"pid {int(ws[0])} not found")

    legitimate_processes: list[Process] = []
    for p in processes.values():
        if p.end_time == (1 << 32):
            logging.warning(f"pid {p.pid} {p.program} has no end time")
        else:
            legitimate_processes.append(p)
    trace = generate_trace_json(legitimate_processes)
    with open(output_json, "w") as f:
        f.write(trace)

    plot_processes(legitimate_processes, output_image)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse strace log")
    parser.add_argument("--log", type=str, help="strace log file", required=True)
    parser.add_argument(
        "--output_json", type=str, help="output json file", required=True
    )
    parser.add_argument(
        "--output_image", type=str, help="output plot file", required=True
    )
    args = parser.parse_args()
    main(args.log, args.output_json, args.output_image)
