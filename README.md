# COM Module ICMP Network Monitor

A lightweight Linux-based network monitoring tool for monitoring multiple COM modules using **ICMP ping**.

The monitor checks each configured COM module every **60 seconds** and records network connectivity, TTL, packet loss, and RTT statistics.

---

## Features

* Monitor multiple COM module IP addresses
* ICMP Echo Request monitoring
* Send 4 ICMP packets per device
* Check ONLINE / OFFLINE / DEGRADED status
* Capture TTL value
* Calculate packet loss
* Measure RTT
* Record minimum, average, and maximum RTT
* Separate status and error logs
* Store detailed monitoring data in CSV format
* Automatically repeat monitoring every 60 seconds
* IP addresses managed through a separate configuration file

---

## Project Structure

```text
com_monitor/
│
├── com_monitor.py
├── ip_list.txt
├── README.md
├── .gitignore
│
└── logs/
    ├── status.log
    ├── error.log
    └── network_status.csv
```

---

## Requirements

### Operating System

Linux

### Required Software

* Python 3
* Linux `ping` command
* Git (optional, for version control)

Check Python:

```bash
python3 --version
```

Check ping:

```bash
ping -V
```

---

## Configuration

COM module IP addresses are configured in:

```text
ip_list.txt
```

### Format

```text
COM_NAME IP_ADDRESS
```

### Example

```text
COM1 10.8.0.25
COM2 10.8.0.26
COM3 10.8.0.27
COM4 10.8.0.28
```

Comments can be added using `#`:

```text
# COM module list

COM1 10.8.0.25
COM2 10.8.0.26
COM3 10.8.0.27
```

Empty lines and lines beginning with `#` are ignored.

---

## ICMP Monitoring

The script uses the Linux `ping` command to perform ICMP monitoring.

For each COM module, the script executes:

```bash
ping -c 4 -W 2 <IP_ADDRESS>
```

Example:

```bash
ping -c 4 -W 2 10.8.0.25
```

### Parameters

| Parameter | Description                         |
| --------- | ----------------------------------- |
| `-c 4`    | Send 4 ICMP packets                 |
| `-W 2`    | Wait up to 2 seconds for each reply |

The monitoring process therefore uses ICMP Echo Request and ICMP Echo Reply packets.

---

## Monitoring Information

The following information is collected for each COM module.

### Status

Possible statuses:

```text
ONLINE
OFFLINE
DEGRADED
ERROR
```

### ONLINE

The COM module responds to ICMP requests without packet loss.

### OFFLINE

No ICMP replies are received.

### DEGRADED

The COM module responds, but packet loss is detected.

Example:

```text
TX=4
RX=3
LOSS=25%
```

### ERROR

An unexpected monitoring or system error occurred.

---

## TTL

The script extracts the TTL value from the ICMP Echo Reply.

Example:

```text
TTL=64
```

TTL stands for:

```text
Time To Live
```

The TTL value can provide useful information about the network path and the responding device.

---

## Packet Loss

Four packets are sent to every COM module.

Example with no packet loss:

```text
TX=4
RX=4
LOSS=0%
```

Example with packet loss:

```text
TX=4
RX=3
LOSS=25%
```

Example with complete packet loss:

```text
TX=4
RX=0
LOSS=100%
```

---

## RTT Monitoring

RTT means:

```text
Round Trip Time
```

The script records:

* Minimum RTT
* Average RTT
* Maximum RTT
* RTT deviation

Example:

```text
RTT Min : 0.035 ms
RTT Avg : 0.042 ms
RTT Max : 0.050 ms
```

Lower RTT generally indicates a faster network response.

---

## Monitoring Interval

The default monitoring interval is:

```python
PING_INTERVAL = 60
```

This means the complete list of COM modules is checked every:

```text
60 seconds
```

To change the interval, edit `com_monitor.py`.

Example: check every 30 seconds:

```python
PING_INTERVAL = 30
```

Example: check every 5 minutes:

```python
PING_INTERVAL = 300
```

---

## Ping Configuration

The default configuration is:

```python
PING_COUNT = 4
PING_TIMEOUT = 2
PING_INTERVAL = 60
```

Meaning:

```text
4 ICMP packets
2 second timeout
60 second monitoring interval
```

---

## Log Files

All logs are stored in:

```text
logs/
```

### Status Log

```text
logs/status.log
```

Contains normal monitoring results.

Example:

```text
[2026-10-08 12:00:01] COM1 | IP=10.8.0.25 | STATUS=ONLINE | TTL=64 | RX=4/4 | LOSS=0% | AVG_RTT=0.42 ms
```

---

### Error Log

```text
logs/error.log
```

Contains monitoring errors.

Example:

```text
[2026-10-08 12:01:01] PING_TIMEOUT | COM3 | IP=10.8.0.27
```

Possible errors include:

```text
PING_TIMEOUT
PACKET_LOSS
IP_LIST_ERROR
MONITOR_ERROR
```

---

### CSV Log

```text
logs/network_status.csv
```

The CSV file stores detailed monitoring data.

Columns include:

```text
Timestamp
COM
IP
Status
TTL
Packets_Sent
Packets_Received
Packet_Loss_Percent
RTT_Min_ms
RTT_Avg_ms
RTT_Max_ms
RTT_Mdev_ms
Error
```

The CSV file can be opened using Excel or another spreadsheet application.

---

## Installation

Clone or copy the project to the Linux server.

Example:

```bash
cd ~
mkdir com_monitor
cd com_monitor
```

Copy the following files into the directory:

```text
com_monitor.py
ip_list.txt
README.md
.gitignore
```

Create the log directory:

```bash
mkdir -p logs
```

---

## Configure IP Addresses

Edit the IP list:

```bash
nano ip_list.txt
```

Example:

```text
COM1 10.8.0.25
COM2 10.8.0.26
COM3 10.8.0.27
COM4 10.8.0.28
```

Save the file.

Verify:

```bash
cat ip_list.txt
```

---

## Run the Monitor

Make the Python script executable:

```bash
chmod +x com_monitor.py
```

Run:

```bash
./com_monitor.py
```

Alternatively:

```bash
python3 com_monitor.py
```

---

## Example Console Output

```text
==============================================
       COM MODULE ICMP NETWORK MONITOR
==============================================

IP List    : /home/user/com_monitor/ip_list.txt
ICMP Count : 4
Timeout    : 2 seconds
Interval   : 60 seconds

Monitoring started...

====================================================================================================
2026-10-08 12:00:01
----------------------------------------------------------------------------------------------------

COM1       10.8.0.25       ONLINE     TTL=64    RX=4/4 LOSS=0% AVG=0.42 ms

COM2       10.8.0.26       ONLINE     TTL=64    RX=4/4 LOSS=0% AVG=0.61 ms

COM3       10.8.0.27       OFFLINE    TTL=-     RX=0/4 LOSS=100% AVG=-
           ERROR: PING_TIMEOUT
```

After completing the monitoring cycle, the script waits 60 seconds and starts the next cycle.

---

## Stop the Monitor

Press:

```text
Ctrl + C
```

The monitoring process will stop.

---

## Test an IP Manually

Before running the Python monitor, an individual COM module can be tested manually:

```bash
ping -c 4 10.8.0.25
```

Example:

```text
4 packets transmitted, 4 received, 0% packet loss
rtt min/avg/max/mdev = 0.035/0.042/0.050/0.006 ms
```

This is useful for troubleshooting.

---

## Troubleshooting

### IP list not found

Check:

```bash
ls -l ip_list.txt
```

Check the current directory:

```bash
pwd
```

The script normally searches for `ip_list.txt` in the same directory as `com_monitor.py`.

---

### Permission denied

Run:

```bash
chmod +x com_monitor.py
```

Then:

```bash
./com_monitor.py
```

---

### Ping command not found

Check:

```bash
which ping
```

On Debian/Ubuntu systems, install the ping utility if necessary:

```bash
sudo apt install iputils-ping
```

---

### COM module is OFFLINE

Test manually:

```bash
ping -c 4 <COM_MODULE_IP>
```

Example:

```bash
ping -c 4 10.8.0.25
```

Then check:

```text
logs/error.log
```

and:

```text
logs/status.log
```

---

## Git

Initialize the project as a Git repository:

```bash
git init
```

Check the repository:

```bash
git status
```

Add the project files:

```bash
git add com_monitor.py README.md .gitignore
```

Create the initial commit:

```bash
git commit -m "Initial COM module ICMP network monitor"
```

---

## .gitignore

Recommended `.gitignore`:

```text
logs/
__pycache__/
*.pyc
```

This prevents generated log files and Python cache files from being committed to Git.

If `ip_list.txt` contains production/private IP addresses, it is recommended to exclude it from Git:

```text
ip_list.txt
```

An example file can then be created:

```text
ip_list.example.txt
```

Example:

```text
COM1 192.168.1.10
COM2 192.168.1.11
COM3 192.168.1.12
```

---

## Monitoring Flow

```text
              START
                |
                v
         Read ip_list.txt
                |
                v
        Load COM module list
                |
                v
       Select COM module IP
                |
                v
       Send 4 ICMP packets
                |
                v
       Receive ICMP replies
                |
          +-----+-----+
          |           |
          v           v
       Reply        No Reply
          |           |
          v           v
    Get TTL/RTT    OFFLINE
          |
          v
    Calculate loss
          |
          v
    Determine status
          |
     +----+----+
     |         |
     v         v
  Status     Error
   Log        Log
     |
     v
   CSV Log
     |
     v
 Wait 60 seconds
     |
     v
    Repeat
```

---

## Important Limitation

ICMP monitoring confirms that the COM module is **reachable at the network level**.

It does not confirm that the application or service running on the COM module is functioning correctly.

For deeper monitoring, additional checks can be added later:

```text
ICMP
  |
  v
Network Reachability
  |
  v
TCP Port Check
  |
  v
Service Availability
  |
  v
Application Protocol Check
  |
  v
Application Health
```

For example, a TCP port check could verify whether a specific COM module service is listening.

---

## Summary

The COM Module ICMP Network Monitor provides continuous network-level monitoring for multiple COM modules on a Linux server.

The system:

1. Reads COM module IP addresses from `ip_list.txt`.
2. Sends 4 ICMP Echo Request packets.
3. Checks ICMP Echo Replies.
4. Records TTL.
5. Calculates packet loss.
6. Measures RTT statistics.
7. Determines the network status.
8. Writes normal results to `status.log`.
9. Writes errors to `error.log`.
10. Stores detailed results in `network_status.csv`.
11. Repeats the monitoring process every 60 seconds.

This provides a simple and lightweight network monitoring layer for COM modules.
