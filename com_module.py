#!/usr/bin/env python3

# ============================================================
# COM MODULE ICMP NETWORK MONITOR
# ============================================================
#
# Purpose:
#   Monitor multiple COM modules using ICMP ping.
#
# Main functions:
#   1. Read COM module IP addresses from ip_list.txt
#   2. Send 4 ICMP Echo Request packets to each IP
#   3. Check ONLINE / OFFLINE / DEGRADED status
#   4. Read TTL from ICMP Echo Reply
#   5. Calculate packet loss
#   6. Read RTT statistics
#   7. Save normal status information
#   8. Save errors separately
#   9. Save detailed information to CSV
#  10. Repeat monitoring every 60 seconds
#
# Operating System:
#   Linux
#
# Requirements:
#   Python 3
#   Linux ping command
#
# ============================================================


# ============================================================
# IMPORT REQUIRED MODULES
# ============================================================

# subprocess:
# Used to execute the Linux "ping" command.
import subprocess

# re:
# Used to extract TTL, packet loss and RTT values
# from the ping command output.
import re

# csv:
# Used to create and update the CSV monitoring file.
import csv

# os:
# Used for file paths and checking whether files exist.
import os

# time:
# Used to wait between monitoring cycles.
import time

# datetime:
# Used to add timestamps to logs and CSV records.
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

# Get the directory where this Python script is located.
#
# This allows the script to find ip_list.txt and logs/
# even when the script is executed from another directory.
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ------------------------------------------------------------
# IP LIST FILE
# ------------------------------------------------------------

# File containing COM module names and IP addresses.
#
# Example:
#
# COM1 192.168.1.10
# COM2 192.168.1.11
#
IP_LIST_FILE = os.path.join(
    BASE_DIR,
    "ip_list.txt"
)


# ------------------------------------------------------------
# LOG DIRECTORY
# ------------------------------------------------------------

# All monitoring logs are stored inside this directory.
LOG_DIR = os.path.join(
    BASE_DIR,
    "logs"
)


# ------------------------------------------------------------
# LOG FILES
# ------------------------------------------------------------

# Normal network status log.
STATUS_LOG = os.path.join(
    LOG_DIR,
    "status.log"
)


# Error-only log.
ERROR_LOG = os.path.join(
    LOG_DIR,
    "error.log"
)


# Detailed CSV monitoring log.
STATUS_CSV = os.path.join(
    LOG_DIR,
    "network_status.csv"
)


# ------------------------------------------------------------
# PING CONFIGURATION
# ------------------------------------------------------------

# Number of ICMP packets sent to each COM module.
#
# 4 packets are sent during each monitoring cycle.
PING_COUNT = 4


# Maximum time to wait for each ping response.
#
# Value is in seconds.
PING_TIMEOUT = 2


# Time between complete monitoring cycles.
#
# 60 seconds = 1 minute.
PING_INTERVAL = 60


# ============================================================
# CREATE LOG DIRECTORY
# ============================================================

# Create the logs directory if it does not already exist.
#
# exist_ok=True prevents an error if the directory already exists.
os.makedirs(
    LOG_DIR,
    exist_ok=True
)


# ============================================================
# LOAD COM MODULE IP LIST
# ============================================================

def load_ip_list():
    """
    Read COM module names and IP addresses
    from ip_list.txt.

    Expected format:

        COM1 192.168.1.10
        COM2 192.168.1.11
        COM3 192.168.1.12

    Returns:
        List containing COM module information.
    """

    # List used to store all COM modules.
    modules = []

    try:

        # Open the IP list file in read mode.
        with open(
            IP_LIST_FILE,
            "r"
        ) as file:

            # Read the file line by line.
            for line in file:

                # Remove spaces and newline characters.
                line = line.strip()


                # ------------------------------------------------
                # SKIP EMPTY LINES
                # ------------------------------------------------

                if not line:
                    continue


                # ------------------------------------------------
                # SKIP COMMENT LINES
                # ------------------------------------------------

                # Lines beginning with # are comments.
                #
                # Example:
                # # COM module list
                #
                if line.startswith("#"):
                    continue


                # ------------------------------------------------
                # SPLIT LINE
                # ------------------------------------------------

                # Split the line into fields.
                #
                # Example:
                #
                # COM1 192.168.1.10
                #
                # becomes:
                #
                # ["COM1", "192.168.1.10"]
                #
                parts = line.split()


                # ------------------------------------------------
                # VALIDATE LINE
                # ------------------------------------------------

                # A valid line must contain at least:
                #
                #   1. COM name
                #   2. IP address
                #
                if len(parts) < 2:
                    continue


                # First field = COM module name.
                com_name = parts[0]

                # Second field = IP address.
                ip = parts[1]


                # ------------------------------------------------
                # STORE MODULE INFORMATION
                # ------------------------------------------------

                modules.append({
                    "com": com_name,
                    "ip": ip
                })


    except FileNotFoundError:

        # If ip_list.txt does not exist,
        # record the error in the error log.
        log_error(
            "IP_LIST_ERROR",
            f"IP list file not found: {IP_LIST_FILE}"
        )


    # Return all loaded COM modules.
    return modules


# ============================================================
# PING COM MODULE USING ICMP
# ============================================================

def ping_device(ip):
    """
    Send ICMP Echo Request packets to the specified IP.

    Returns:
        Dictionary containing:
            status
            ttl
            transmitted
            received
            packet_loss
            rtt_min
            rtt_avg
            rtt_max
            rtt_mdev
            error
    """

    # ----------------------------------------------------------
    # LINUX PING COMMAND
    # ----------------------------------------------------------
    #
    # Example:
    #
    # ping -c 4 -W 2 192.168.1.10
    #
    # -c 4
    #   Send 4 ICMP packets.
    #
    # -W 2
    #   Wait up to 2 seconds for a reply.
    #
    command = [
        "ping",
        "-c", str(PING_COUNT),
        "-W", str(PING_TIMEOUT),
        ip
    ]


    try:

        # Execute Linux ping command.
        #
        # capture_output=True:
        #   Capture stdout and stderr.
        #
        # text=True:
        #   Return output as normal text.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )


        # Combine normal output and error output.
        output = (
            result.stdout +
            result.stderr
        )


        # ========================================================
        # GET TTL
        # ========================================================
        #
        # Linux ping reply example:
        #
        # 64 bytes from 192.168.1.10:
        # icmp_seq=1 ttl=64 time=0.421 ms
        #
        # Extract:
        #
        # ttl=64
        #

        ttl_values = re.findall(
            r"ttl=(\d+)",
            output,
            re.IGNORECASE
        )


        # If at least one TTL value was found,
        # use the first successful reply.
        if ttl_values:

            ttl = int(
                ttl_values[0]
            )

        else:

            ttl = None


        # ========================================================
        # GET PACKET STATISTICS
        # ========================================================
        #
        # Linux ping summary:
        #
        # 4 packets transmitted,
        # 4 received,
        # 0% packet loss
        #

        packet_match = re.search(
            r"(\d+)\s+packets transmitted,\s+"
            r"(\d+)\s+(?:packets )?received,\s+"
            r"(\d+)%\s+packet loss",
            output,
            re.IGNORECASE
        )


        if packet_match:

            # Number of packets sent.
            transmitted = int(
                packet_match.group(1)
            )

            # Number of packets received.
            received = int(
                packet_match.group(2)
            )

            # Packet loss percentage.
            packet_loss = int(
                packet_match.group(3)
            )

        else:

            # If ping statistics cannot be found,
            # assume all packets were lost.
            transmitted = PING_COUNT
            received = 0
            packet_loss = 100


        # ========================================================
        # GET RTT STATISTICS
        # ========================================================
        #
        # Linux ping example:
        #
        # rtt min/avg/max/mdev =
        # 0.035/0.042/0.050/0.006 ms
        #

        rtt_match = re.search(
            r"=\s*"
            r"([\d.]+)/"
            r"([\d.]+)/"
            r"([\d.]+)/"
            r"([\d.]+)"
            r"\s*ms",
            output
        )


        if rtt_match:

            # Minimum Round Trip Time.
            rtt_min = float(
                rtt_match.group(1)
            )

            # Average Round Trip Time.
            rtt_avg = float(
                rtt_match.group(2)
            )

            # Maximum Round Trip Time.
            rtt_max = float(
                rtt_match.group(3)
            )

            # RTT deviation.
            rtt_mdev = float(
                rtt_match.group(4)
            )

        else:

            rtt_min = None
            rtt_avg = None
            rtt_max = None
            rtt_mdev = None


        # ========================================================
        # DETERMINE DEVICE STATUS
        # ========================================================

        # If ping command succeeded and at least one
        # packet was received, the device is reachable.
        if (
            result.returncode == 0
            and received > 0
        ):

            # No packet loss.
            if packet_loss == 0:

                status = "ONLINE"
                error = ""

            # Some packets were lost.
            else:

                status = "DEGRADED"
                error = "PACKET_LOSS"


        # No ICMP replies were received.
        elif received == 0:

            status = "OFFLINE"
            error = "PING_TIMEOUT"


        # Unexpected condition.
        else:

            status = "ERROR"
            error = "PING_ERROR"


        # Return all monitoring information.
        return {

            "status": status,

            "ttl": ttl,

            "transmitted": transmitted,

            "received": received,

            "packet_loss": packet_loss,

            "rtt_min": rtt_min,

            "rtt_avg": rtt_avg,

            "rtt_max": rtt_max,

            "rtt_mdev": rtt_mdev,

            "error": error
        }


    except Exception as e:

        # Catch unexpected Python/system errors.
        return {

            "status": "ERROR",

            "ttl": None,

            "transmitted": 0,

            "received": 0,

            "packet_loss": 100,

            "rtt_min": None,

            "rtt_avg": None,

            "rtt_max": None,

            "rtt_mdev": None,

            "error": str(e)
        }


# ============================================================
# WRITE STATUS LOG
# ============================================================

def log_status(com, ip, result):
    """
    Write normal monitoring information
    to status.log.
    """

    # Generate current timestamp.
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # Convert TTL to display format.
    ttl = (
        result["ttl"]
        if result["ttl"] is not None
        else "-"
    )


    # Convert average RTT to display format.
    avg = (
        f"{result['rtt_avg']:.2f} ms"
        if result["rtt_avg"] is not None
        else "-"
    )


    # Create log message.
    message = (
        f"[{timestamp}] "
        f"{com} | "
        f"IP={ip} | "
        f"STATUS={result['status']} | "
        f"TTL={ttl} | "
        f"RX={result['received']}/"
        f"{result['transmitted']} | "
        f"LOSS={result['packet_loss']}% | "
        f"AVG_RTT={avg}"
    )


    # Append message to status.log.
    with open(
        STATUS_LOG,
        "a"
    ) as file:

        file.write(
            message + "\n"
        )


# ============================================================
# WRITE ERROR LOG
# ============================================================

def log_error(error_type, message):
    """
    Write errors to error.log.
    """

    # Generate timestamp.
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # Open error log in append mode.
    with open(
        ERROR_LOG,
        "a"
    ) as file:

        file.write(
            f"[{timestamp}] "
            f"{error_type} | "
            f"{message}\n"
        )


# ============================================================
# WRITE CSV MONITORING DATA
# ============================================================

def save_csv(com, ip, result):
    """
    Save monitoring information to network_status.csv.
    """

    # Check whether CSV file already exists.
    file_exists = os.path.exists(
        STATUS_CSV
    )


    # Generate timestamp.
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    # Open CSV file in append mode.
    with open(
        STATUS_CSV,
        "a",
        newline=""
    ) as file:

        # Create CSV writer.
        writer = csv.writer(file)


        # --------------------------------------------------------
        # CREATE CSV HEADER
        # --------------------------------------------------------

        # Header is written only when the file
        # is created for the first time.
        if not file_exists:

            writer.writerow([
                "Timestamp",
                "COM",
                "IP",
                "Status",
                "TTL",
                "Packets_Sent",
                "Packets_Received",
                "Packet_Loss_Percent",
                "RTT_Min_ms",
                "RTT_Avg_ms",
                "RTT_Max_ms",
                "RTT_Mdev_ms",
                "Error"
            ])


        # --------------------------------------------------------
        # WRITE MONITORING DATA
        # --------------------------------------------------------

        writer.writerow([

            timestamp,

            com,

            ip,

            result["status"],

            result["ttl"]
            if result["ttl"] is not None
            else "",

            result["transmitted"],

            result["received"],

            result["packet_loss"],

            result["rtt_min"]
            if result["rtt_min"] is not None
            else "",

            result["rtt_avg"]
            if result["rtt_avg"] is not None
            else "",

            result["rtt_max"]
            if result["rtt_max"] is not None
            else "",

            result["rtt_mdev"]
            if result["rtt_mdev"] is not None
            else "",

            result["error"]
        ])


# ============================================================
# DISPLAY RESULT ON TERMINAL
# ============================================================

def print_result(com, ip, result):
    """
    Display the current COM module status
    on the Linux terminal.
    """

    # Convert TTL to text.
    ttl = (
        str(result["ttl"])
        if result["ttl"] is not None
        else "-"
    )


    # Convert average RTT to text.
    avg = (
        f"{result['rtt_avg']:.2f} ms"
        if result["rtt_avg"] is not None
        else "-"
    )


    # Print main result.
    print(
        f"{com:<10} "
        f"{ip:<16} "
        f"{result['status']:<10} "
        f"TTL={ttl:<5} "
        f"RX={result['received']}/"
        f"{result['transmitted']} "
        f"LOSS={result['packet_loss']}% "
        f"AVG={avg}"
    )


    # If an error occurred,
    # display it below the main result.
    if result["error"]:

        print(
            f"           "
            f"ERROR: {result['error']}"
        )


# ============================================================
# CHECK ALL COM MODULES
# ============================================================

def check_all_modules():
    """
    Load all COM modules from ip_list.txt,
    ping each module and save the results.
    """

    # Load current IP list.
    #
    # The file is read during every monitoring cycle.
    # Therefore IP changes can be detected without
    # modifying the Python script.
    modules = load_ip_list()


    # ----------------------------------------------------------
    # CHECK WHETHER MODULES WERE FOUND
    # ----------------------------------------------------------

    if not modules:

        log_error(
            "IP_LIST_ERROR",
            "No valid COM modules found"
        )

        print(
            "No COM modules found."
        )

        return


    # ----------------------------------------------------------
    # DISPLAY MONITORING HEADER
    # ----------------------------------------------------------

    print()

    print(
        "=" * 100
    )

    print(
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print(
        "-" * 100
    )


    # ----------------------------------------------------------
    # CHECK EACH COM MODULE
    # ----------------------------------------------------------

    for module in modules:

        # Get COM module name.
        com = module["com"]

        # Get COM module IP address.
        ip = module["ip"]


        # ------------------------------------------------------
        # SEND ICMP PING
        # ------------------------------------------------------

        result = ping_device(
            ip
        )


        # ------------------------------------------------------
        # DISPLAY RESULT
        # ------------------------------------------------------

        print_result(
            com,
            ip,
            result
        )


        # ------------------------------------------------------
        # SAVE STATUS
        # ------------------------------------------------------

        log_status(
            com,
            ip,
            result
        )


        # ------------------------------------------------------
        # SAVE CSV
        # ------------------------------------------------------

        save_csv(
            com,
            ip,
            result
        )


        # ------------------------------------------------------
        # SAVE ERROR
        # ------------------------------------------------------

        # Only errors are written to error.log.
        if result["error"]:

            log_error(
                result["error"],
                f"{com} | IP={ip}"
            )


# ============================================================
# MAIN MONITORING LOOP
# ============================================================

def main():
    """
    Main program.

    The monitoring process runs continuously.
    """

    # ----------------------------------------------------------
    # DISPLAY PROGRAM INFORMATION
    # ----------------------------------------------------------

    print()

    print(
        "=============================================="
    )

    print(
        "       COM MODULE ICMP NETWORK MONITOR"
    )

    print(
        "=============================================="
    )

    print()

    print(
        f"IP List    : {IP_LIST_FILE}"
    )

    print(
        f"ICMP Count : {PING_COUNT}"
    )

    print(
        f"Timeout    : {PING_TIMEOUT} seconds"
    )

    print(
        f"Interval   : {PING_INTERVAL} seconds"
    )

    print()

    print(
        "Monitoring started..."
    )

    print(
        "Press Ctrl+C to stop."
    )


    # ----------------------------------------------------------
    # CONTINUOUS MONITORING LOOP
    # ----------------------------------------------------------

    while True:

        try:

            # Check all configured COM modules.
            check_all_modules()


            # Wait before starting the next monitoring cycle.
            time.sleep(
                PING_INTERVAL
            )


        except KeyboardInterrupt:

            # Ctrl+C was pressed.
            print()

            print(
                "Monitoring stopped."
            )

            break


        except Exception as e:

            # Catch unexpected monitoring errors.
            log_error(
                "MONITOR_ERROR",
                str(e)
            )


            # Wait before retrying.
            time.sleep(
                PING_INTERVAL
            )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

# This condition ensures that main() is executed only
# when this file is run directly.
if __name__ == "__main__":

    main()
