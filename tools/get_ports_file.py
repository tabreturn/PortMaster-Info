import requests
import json

repos = {"main": "https://api.github.com/repos/PortsMaster/PortMaster-Releases/releases/latest",
         "multiverse":"https://api.github.com/repos/PortsMaster-MV/PortMaster-Multiverse/releases/latest"
         }


ports = {"ports":{}}

for repo in repos:
    latest_release = requests.get(repos[repo])

    for item in latest_release.json()["assets"]:
        if item["name"] == "ports.json":
            r = requests.get(item["browser_download_url"], allow_redirects=True)
            portsJson = r.json()["ports"]
            for port in portsJson:
                portsJson[port]["source"]["repo"] = repo
                ports["ports"][port] = portsJson[port]


with open("ports.json", "w",encoding="utf8") as outfile:
    outfile.write(json.dumps(ports,indent=2,sort_keys=True))