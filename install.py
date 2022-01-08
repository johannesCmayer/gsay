from os.path import expanduser
import os

install_target = expanduser("~/bin/gsay")

with open(install_target, 'w') as f:
    s = \
        "#!/bin/bash\n" + \
        "\n" + \
        f"python {os.path.dirname(os.path.realpath(__file__))}/main.py $@" \

    f.write(s)
    os.system(f"chmod +x {install_target}")