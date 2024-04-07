# DHCP Server

This is a DHCP (Dynamic Host Configuration Protocol) server implemented using socket programming and threading in Python. The server assigns IP addresses to clients dynamically, ensures that the same IP address cannot be assigned twice, requires clients to request the renewal of IP addresses before expiry time, and has a maximum of 5 IP addresses assigned at a time.

## Features

- Dynamic assignment of IP addresses to clients.
- Prevention of duplicate IP address assignments.
- Renewal of IP addresses requested by clients before expiry time.
- Maximum of 5 IP addresses assigned at a time.
