import os
import time
import subprocess
import argparse
import json
import xmltodict
from lxml import etree



def get_lscpu_info():
    lscpu_info = {}
    try:
        lscpu_output = (subprocess.check_output("lscpu", shell=True).strip()).decode()
        lscpu_lines = lscpu_output.split('\n')
        for line in lscpu_lines:
            if line.startswith('Architecture:'):
                lscpu_info["Architecture"] = line.split('Architecture:')[-1].strip()
            elif line.startswith('CPU(s):'):
                lscpu_info["CPUs"] = line.split('CPU(s):')[-1].strip()
            elif line.startswith('Thread(s) per core:'):
                lscpu_info["Threads per core"] = line.split('Thread(s) per core:')[-1].strip()
            elif line.startswith('Core(s) per socket:'):
                lscpu_info["Cores per socket"] = line.split('Core(s) per socket:')[-1].strip()
            elif line.startswith('Socket(s):'):
                lscpu_info["Sockets"] = line.split('Socket(s):')[-1].strip()
            elif line.startswith('NUMA node(s):'):
                lscpu_info["NUMA nodes"] = line.split('NUMA node(s):')[-1].strip()
            elif line.startswith('Vendor ID:'):
                lscpu_info["Vendor ID"] = line.split('Vendor ID:')[-1].strip()
            elif line.startswith('Model name:'):
                lscpu_info["Model name"] = line.split('Model name:')[-1].strip()
            elif line.startswith('NUMA node'):
                splitted_line = line.split(':')
                lscpu_info[splitted_line[0]] = splitted_line[-1].strip()
            elif 'cache:' in line:
                splitted_line = line.split(':')
                lscpu_info[splitted_line[0]] = splitted_line[-1].strip()

    except subprocess.CalledProcessError as e:
        print(e.output)

    return lscpu_info


def get_intel_pstate_info():
    files = ["status", "num_pstates", "max_perf_pct", "min_perf_pct", "turbo_pct"]
    pstate_info = {}
    try:
        if os.path.isfile("/sys/devices/system/cpu/intel_pstate/no_turbo"):
            turbo_output = (subprocess.check_output("cat /sys/devices/system/cpu/intel_pstate/no_turbo",
                                                    shell=True).strip()).decode()
            pstate_info["Turbo Boost"] = "Enabled" if turbo_output == "0" else "Disabled"

        for file in files:
            if not os.path.isfile(f'/sys/devices/system/cpu/intel_pstate/{file}'):
                continue
            pstate_info[file.replace("_", " ", ).title()] = (
                subprocess.check_output(f"cat /sys/devices/system/cpu/intel_pstate/{file}",
                                        shell=True).strip()).decode()

    except subprocess.CalledProcessError as e:
        print(e.output)

    return pstate_info


def get_cpu_frequency_and_microcode_info(cpus):
    files = ["cpuinfo_max_freq", "cpuinfo_min_freq", "base_frequency", "scaling_max_freq", "scaling_min_freq",
             "scaling_cur_freq", "scaling_driver", "scaling_governor"]
    freq_info = {}
    microcode_info = {}
    try:
        for i in range(0, int(cpus)):
            tmp = {}
            for file in files:
                if not os.path.isfile(f"/sys/devices/system/cpu/cpu{i}/cpufreq/{file}"):
                    continue
                tmp[file.replace("_", " ", ).title()] = (
                    subprocess.check_output(f"cat /sys/devices/system/cpu/cpu{i}/cpufreq/{file}",
                                            shell=True).strip()).decode()
            freq_info[f"Cpu {i}"] = tmp

            if not os.path.isfile(f"/sys/devices/system/cpu/cpu{i}/microcode/version"):
                continue
            microcode_info[f"Cpu {i}"] = {}
            microcode_info[f"Cpu {i}"]["Version"] = (
                subprocess.check_output(f"cat /sys/devices/system/cpu/cpu{i}/microcode/version",
                                        shell=True).strip()).decode()

    except subprocess.CalledProcessError as e:
        print(e.output)

    return freq_info, microcode_info


def get_caches_info(path):
    files = ["coherency_line_size", "level", "number_of_sets", "physical_line_partition", "size",
             "type", "ways_of_associativity"]
    caches_info = {}

    try:
        listdir = os.listdir(path)
        for name in sorted(listdir):
            if "index" in name and os.path.isdir(f'{path}/{name}'):
                caches_info[name] = {}
                for file in files:
                    if not os.path.isfile(f'{path}/{name}/{file}'):
                        continue
                    caches_info[name][file.replace("_", " ", ).title()] = (
                        subprocess.check_output(f'cat {path}/{name}/{file}', shell=True).strip()).decode()

    except subprocess.CalledProcessError as e:
        print(e.output)

    return caches_info


def get_nic_info():
    networks = []
    try:
        network_output = (
            subprocess.check_output("lshw -class network -xml -sanitize", shell=True).strip()).decode()

        xslt_root = etree.fromstring(network_output)
        networks_list = xslt_root.findall("node[@class='network']")

        for e in networks_list:
            network = xmltodict.parse(etree.tostring(e), dict_constructor=dict)
            networks.append(network.get("node"))

    except subprocess.CalledProcessError as e:
        print(e.output)

    return networks


def get_memory_info():
    memories = []
    try:
        memory_output = (
            subprocess.check_output("lshw -class memory -xml -sanitize", shell=True).strip()).decode()

        xslt_root = etree.fromstring(memory_output)
        memories_list = xslt_root.findall("node[@class='memory']")

        for e in memories_list:
            memory = xmltodict.parse(etree.tostring(e), dict_constructor=dict)
            memories.append(memory.get("node"))
    except subprocess.CalledProcessError as e:
        print(e.output)


    memory_devices = []
    memory = {}
    try:
        memory_output = (
            subprocess.check_output("dmidecode -t memory", shell=True).strip()).decode()

        memory_output_lines = memory_output.split("\n")
        for i,line in enumerate(memory_output_lines):
            if "Handle " in line:
                if len(memory) != 0:
                    memory_devices.append(memory)
                memory = {
                    "Description": line,
                    "Type": memory_output_lines[i+1] if i+1 < len(memory_output_lines) else "-"
                }
            if ": " in line:
                splitted_line = line.split(": ")
                memory[splitted_line[0].strip().title()] = splitted_line[-1].strip()
        if len(memory) != 0:
            memory_devices.append(memory)
    except subprocess.CalledProcessError as e:
        print(e.output)

    return {"Memory": memories, "Memory Devices": memory_devices}


def get_storage_info():
    storages = []
    try:
        storage_output = (
            subprocess.check_output("lshw -class storage -class disk -xml -sanitize", shell=True).strip()).decode()

        xslt_root = etree.fromstring(storage_output)
        disks_list = xslt_root.findall("node/node[@class='disk']")

        for e in disks_list:
            disk = xmltodict.parse(etree.tostring(e), dict_constructor=dict)
            storages.append(disk.get("node"))

    except subprocess.CalledProcessError as e:
        print(e.output)

    return storages


def get_sst_info(sst_command):
    sst = {}
    try:
        datetime_str = time.strftime("%Y%m%d-%H%M%S")
        filename = f'out-sst-info-{datetime_str}.json'
        subprocess.check_output(f'{sst_command} -o {filename} -f json perf-profile info', shell=True)

        if not os.path.isfile(filename):
            return {}

        f = open(filename, )
        sst = json.load(f)
        f.close()

        subprocess.check_output(f'rm {filename}', shell=True)

    except subprocess.CalledProcessError as e:
        print(e.output)

    return sst


def get_cpu_info():
    cpu_info = get_lscpu_info()

    try:
        ht_output = (subprocess.check_output("cat /sys/devices/system/cpu/smt/active", shell=True).strip()).decode()
        cpu_info["Hyperthreading"] = "Enabled" if ht_output == "1" else "Disabled"
    except subprocess.CalledProcessError as e:
        print(e.output)

    if os.path.isdir('/sys/devices/system/cpu/intel_pstate'):
        cpu_info["Intel Pstate"] = get_intel_pstate_info()

    if "CPUs" in cpu_info and cpu_info["CPUs"] != "" and os.path.isdir('/sys/devices/system/cpu/cpu0/cpufreq/'):
        cpu_info["Frequency"], cpu_info["Microcode"] = get_cpu_frequency_and_microcode_info(cpu_info["CPUs"])

    return cpu_info


def get_bios_version():
    bios_version = ""
    try:
        bios_version = (subprocess.check_output("dmidecode -s bios-version", shell=True).strip()).decode()
    except subprocess.CalledProcessError as e:
        print(e.output)

    return bios_version


def get_cmdline():
    cmdline = ""
    try:
        cmdline = (subprocess.check_output("cat /proc/cmdline", shell=True).strip()).decode()
    except subprocess.CalledProcessError as e:
        print(e.output)

    return cmdline


def get_distr_info():
    distr = {}
    try:
        lsb_output = (subprocess.check_output("cat /etc/lsb-release", shell=True).strip()).decode()
        lsb_lines = lsb_output.split("\n")
        for line in lsb_lines:
            distr[line.split("=")[0].replace("_", " ").title()] = line.split("=")[-1]
    except subprocess.CalledProcessError as e:
        print(e.output)

    return distr


def get_kernel():
    kernel = ""
    try:
        kernel = (subprocess.check_output("uname -r", shell=True).strip()).decode()
    except subprocess.CalledProcessError as e:
        print(e.output)

    return kernel


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--sst_executable', help='The path of the sst (speed select technology) tool executable')
    parser.add_argument('--output', help='The path of the output file')
    args = parser.parse_args()

    sst_command = args.sst_executable if args.sst_executable is not None else "intel-speed-select"

    total_info = {"Cpu Info": get_cpu_info(), "BIOS Version": get_bios_version()}

    if os.path.isdir('/sys/devices/system/cpu/cpu0/cache'):
        total_info["Caches Info"] = get_caches_info('/sys/devices/system/cpu/cpu0/cache')

    total_info["Command Line"] = get_cmdline()
    total_info["Distribution Info"] = get_distr_info()
    total_info["Kernel Version"] = get_kernel()

    total_info["Network Info"] = get_nic_info()
    total_info["Memory Info"] = get_memory_info()
    total_info["Storage Info"] = get_storage_info()
    sst = get_sst_info(sst_command)
    total_info["Intel SST"] = sst if sst != {} else "Not-supported"

    datetime_str = time.strftime("%Y%m%d-%H%M%S")
    filename = args.output if args.output is not None and args.output != "" \
        else f"./platform_fingerprint_{datetime_str}.json"
    with open(filename, 'w') as f:
        json.dump(total_info, f)

    print(f"Check the file: {filename}")
