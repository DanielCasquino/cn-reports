from socket import (
    socket,
    AF_INET,
    SOCK_RAW,
    getprotobyname,
    IPPROTO_IP,
    IP_TTL,
    gethostbyname,
    gaierror,
    htons,
    timeout,
)
import os
import struct
import time
import select

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2


def checksum(source_string):
    """Calculate the checksum of the input string."""
    csum = 0
    count_to = (len(source_string) // 2) * 2
    count = 0

    while count < count_to:
        this_val = source_string[count + 1] * 256 + source_string[count]
        csum = csum + this_val
        csum = csum & 0xFFFFFFFF
        count += 2

    if count_to < len(source_string):
        csum = csum + source_string[-1]
        csum = csum & 0xFFFFFFFF

    csum = (csum >> 16) + (csum & 0xFFFF)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xFFFF
    answer = answer >> 8 | (answer << 8 & 0xFF00)
    return answer


def build_packet():
    """Build the ICMP echo request packet."""
    my_checksum = 0
    my_id = os.getpid() & 0xFFFF  # Use PID as packet ID
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, my_id, 1)
    data = struct.pack("d", time.time())
    my_checksum = checksum(header + data)
    if os.name == "posix":
        my_checksum = htons(my_checksum) & 0xFFFF
    else:
        my_checksum = htons(my_checksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, my_id, 1)
    return header + data


def get_route(hostname):
    """Perform a traceroute to the specified hostname."""
    try:
        dest_addr = gethostbyname(hostname)
        print(f"Traceroute to {hostname} ({dest_addr}), {MAX_HOPS} hops max:\n")
    except gaierror as e:
        print(f"Unable to resolve hostname {hostname}: {e}")
        return
    for ttl in range(1, MAX_HOPS + 1):
        for _ in range(TRIES):
            with socket(AF_INET, SOCK_RAW, getprotobyname("icmp")) as my_socket:
                my_socket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack("I", ttl))
                my_socket.settimeout(TIMEOUT)
                try:
                    packet = build_packet()
                    my_socket.sendto(packet, (hostname, 0))
                    t = time.time()
                    ready = select.select([my_socket], [], [], TIMEOUT)
                    if ready[0] == []:  # Timeout
                        print(f"{ttl} * * * Request timed out.")
                        continue

                    rec_packet, addr = my_socket.recvfrom(1024)
                    header_b = rec_packet[20:28]
                    types, code, chk, id, sequence = struct.unpack("bbHHh", header_b)
                    time_received = time.time()

                    if types == 11:  # Time exceeded
                        print(
                            f"{ttl} {addr[0]} rtt={(time_received - t) * 1000:.2f} ms"
                        )
                        break
                    elif types == 3:  # Destination unreachable
                        print(
                            f"{ttl} {addr[0]} rtt={(time_received - t) * 1000:.2f} ms (Destination unreachable)"
                        )
                        break
                    elif types == 0:  # Echo reply
                        print(
                            f"{ttl} {addr[0]} rtt={(time_received - t) * 1000:.2f} ms (Reached destination)"
                        )
                        return
                    else:
                        print(f"{ttl} Unexpected ICMP type {types}")
                        break
                except timeout:
                    print(f"{ttl} * * * Request timed out.")
                    continue
                except Exception as e:
                    print(f"{ttl} Error: {e}")
                    break


def main():
    get_route("google.com")


if __name__ == "__main__":
    main()
