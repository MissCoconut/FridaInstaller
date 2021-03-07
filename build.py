#!/user/bin/env python3
import lzma
import os
import shutil
import zipfile

import requests

PATH_BASE = os.path.abspath(os.path.dirname(__file__))
PATH_BASE_MODULE = os.path.join(PATH_BASE, "base")
PATH_BUILDS = os.path.join(PATH_BASE, "builds")
PATH_DOWNLOADS = os.path.join(PATH_BASE, "downloads")


def traverse_path_to_list(file_list, path):
    for dp, dn, fn in os.walk(path):
        for f in fn:
            if f == "placeholder" or f == ".gitkeep":
                continue
            file_list.append(os.path.join(dp, f))


def download_file(url, path):
    file_name = url[url.rfind("/") + 1:]

    print("Downloading '{0}' to '{1}'.".format(file_name, path))

    if os.path.exists(path):
        return

    r = requests.get(url, allow_redirects = True)
    with open(path, 'wb') as f:
        f.write(r.content)

    print("Done.")


def extract_file(archive_path, dest_path):
    print("Extracting '{0}' to '{1}'.".format(os.path.basename(archive_path), os.path.basename(dest_path)))

    with lzma.open(archive_path) as f:
        file_content = f.read()
        path = os.path.dirname(dest_path)

        if not os.path.exists(path):
            os.makedirs(path)

        with open(dest_path, "wb") as out:
            out.write(file_content)


def create_module_prop(path, frida_release):
    # Create module.prop file.
    module_prop = """id=magiskfrida
name=InstallFrida
version=v{0}
versionCode={1}
author=MissCoconut
description=install frida-server to /system/bin directory
support=None
minMagisk=1530""".format(frida_release, frida_release.replace(".", ""))

    with open(os.path.join(path, "module.prop"), "w", newline = '\n') as f:
        f.write(module_prop)


def create_module(platform, frida_release):
    # Create directory.
    module_dir = os.path.join(PATH_BUILDS, platform)
    module_zip = os.path.join(PATH_BUILDS, "MagiskFrida-{0}-{1}.zip".format(frida_release, platform))

    if os.path.exists(module_dir):
        shutil.rmtree(module_dir)

    if os.path.exists(module_zip):
        os.remove(module_zip)

    # Copy base module into module dir.
    shutil.copytree(PATH_BASE_MODULE, module_dir)

    # cd into module directory.
    os.chdir(module_dir)

    # Create module.prop.
    create_module_prop(module_dir, frida_release)

    _frida32 = os.path.join(PATH_DOWNLOADS, "frida-server-14.2.13-android-arm")
    _frida64 = os.path.join(PATH_DOWNLOADS, "frida-server-14.2.13-android-arm64")
    os.mkdir(os.path.join(module_dir, "system/bin/"))
    shutil.copyfile(_frida32, os.path.join(module_dir, "system/bin/frida-server-32"))
    shutil.copyfile(_frida64, os.path.join(module_dir, "system/bin/frida-server-64"))

    # Create flashable zip.
    print("Building Magisk module.")

    file_list = ["install.sh", "module.prop"]

    traverse_path_to_list(file_list, "./common")
    traverse_path_to_list(file_list, "./system")
    traverse_path_to_list(file_list, "./META-INF")

    with zipfile.ZipFile(module_zip, "w") as zf:
        for file_name in file_list:
            path = os.path.join(module_dir, file_name)

            if not os.path.exists(path):
                print("File {0} does not exist..".format(path))
                continue

            zf.write(path, arcname = file_name)


def main():
    # Create necessary folders.
    if not os.path.exists(PATH_DOWNLOADS):
        os.makedirs(PATH_DOWNLOADS)

    if not os.path.exists(PATH_BUILDS):
        os.makedirs(PATH_BUILDS)

    create_module("arm_all", "14.2.13")
    print("Done.")


if __name__ == "__main__":
    main()
