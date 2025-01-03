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
    full_command: str


def plot_processes(
    *,
    processes: list[Process],
    image_file: str,
    minimum_duration: int,
    title: str,
    width: int,
    height: int,
) -> None:
    processes = list(
        filter(lambda p: p.end_time > p.start_time + minimum_duration, processes)
    )
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
    logging.info(f"Maximal number of processes running concurrently: {max_vcpu}")

    fig, ax = plt.subplots(dpi=100, figsize=(128, 6))
    ax.set_xlim(0, max_time - offset_time)
    ax.set_xlabel("Time (sec)")
    ax.set_xticks(range(0, max_time - offset_time, 50))
    ax.set_ylim(0, max_vcpu)
    ax.set_yticks([])

    program_to_color: dict[str, str] = {"julia": "blue", "as": "red", "ld": "green"}

    for i, p in enumerate(processes):
        s = p.start_time - offset_time
        e = p.end_time - offset_time
        v = process_to_vcpu[i]
        logging.debug(f"{p.program} {s} {e} {v}")

        program_name = os.path.basename(p.program)
        r = patches.Rectangle(
            (s, v),
            e - s,
            1.0,
            facecolor=(
                "none"
                if program_name not in program_to_color
                else program_to_color[program_name]
            ),
            edgecolor="black",
        )
        ax.add_patch(r)

        rx, ry = r.get_xy()
        cx = rx + r.get_width() / 2.0
        cy = ry + r.get_height() / 2.0

        text = program_name
        if e - s > 100:
            text += f" ({e - s} sec) (PID: {p.pid})"
        ax.annotate(
            text,
            (cx, cy),
            color="black",
            weight="bold",
            fontsize=6,
            ha="center",
            va="center",
        )

    logging.debug(f"Saving the plot to {image_file} with title {title}")
    fig.suptitle(title, fontsize=16, fontweight="bold", color="black")
    fig.savefig(image_file)


def parse_execve_line(line: str) -> Process:
    # Parse execve line of strace output. For example:
    # 1662893 1735832847 execve("/usr/bin/make", ["make", "O=/tmp/julia_build", "-j", "4"], 0x7ffc0affe6e0 /* 74 vars */) = 0
    # The first number is the pid, the second number is the time, and the third string is the program name.
    ws = line.replace("(", " ").replace('"', " ").split()
    pid = int(ws[0])
    time = int(ws[1])
    program = ws[3]

    full_command_in_log = ""
    in_full_command = False
    for c in line:
        if c == "[":
            in_full_command = True
        if in_full_command:
            full_command_in_log += c
        if c == "]":
            in_full_command = False
    full_command = " ".join(
        full_command_in_log.replace("[", "").replace("]", "").replace('"', "")
    )

    return Process(
        pid=pid,
        start_time=time,
        end_time=(1 << 32),
        program=program,
        full_command=full_command,
    )


def get_processes_from_log(log_file: str) -> list[Process]:
    # Key: PID, Value: Process
    processes: dict[int, Process] = {}
    with open(log_file, "r") as f:
        for line in f:
            line = line.replace("(", " ").replace('"', " ")
            ws = line.split()
            if len(ws) > 2 and ws[2] == "execve":
                p = parse_execve_line(line)
                processes[p.pid] = p
            if len(ws) > 2 and ws[2] == "exit" or ws[2] == "exit_group":
                if int(ws[0]) in processes:
                    processes[int(ws[0])].end_time = int(ws[1])
                else:
                    logging.warning(
                        f"Cannot find execve corresponding to PID {int(ws[0])}"
                    )

    legitimate_processes: list[Process] = []
    for p in processes.values():
        if p.end_time == (1 << 32):
            logging.warning(f"pid {p.pid} {p.program} has no end time")
        else:
            legitimate_processes.append(p)
    return legitimate_processes


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse strace log")
    parser.add_argument("--log", type=str, help="strace log file", required=True)
    parser.add_argument(
        "--output_image", type=str, help="output plot file", required=True
    )
    parser.add_argument(
        "--minimum_duration",
        type=int,
        help="The minimum duration of a process to be plotted. Shorter processes are omitted.",
        default=5,
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Title of the plot. When you don't specify this, the path to the log file is used.",
        default=None,
    )
    parser.add_argument(
        "--width", type=int, help="Width of the figure in pixels", default=12800
    )
    parser.add_argument(
        "--height", type=int, help="Height of the figure in pixels", default=800
    )
    args = parser.parse_args()

    title = args.title
    if title is None:
        title = args.log
    processes = get_processes_from_log(args.log)
    plot_processes(
        processes=processes,
        image_file=args.output_image,
        minimum_duration=args.minimum_duration,
        title=title,
        width=args.width,
        height=args.height,
    )


if __name__ == "__main__":
    main()
