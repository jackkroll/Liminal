import nmap

scanner = nmap.PortScanner()

hardware_name="aml-s905x-cc"
district_suffix="district.lok12.org"
search_limit ="24"
target_address = hardware_name + "." + district_suffix + "/" + search_limit
options = "-p 80"


scanner.scan(target_address, arguments=options)
for host in scanner.all_hosts():
    if hardware_name + "." + district_suffix == scanner[host].hostname():
        print(host)

if len(scanner.all_hosts()) == 0:
    print("No connections seen")
