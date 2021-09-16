# Platform fingerprint

To get the current fingerprint of a Linux platform, you should run the script get-platform-fingerprint.py.
To get the full output, the platform should have installed the commands: `lscpu, lshw, dmidecode, uname`
and the intel-speed-select tool.

Install the requirements:
```console
pip3 install -r requirements.txt
```

Run the script as root:
```console
python3 get-platform-fingerprint.py --sst_executable=/root/intel-speed-select-utility-src-packages/intel-speed-select-v1.10/intel-speed-select --output=./output.json
```

