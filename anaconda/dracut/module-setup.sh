#!/bin/bash
# module-setup.sh for anaconda

check() {
    [[ $hostonly ]] && return 1
    return 255 # this module is optional
}

depends() {
    echo img-lib dmsquash-live
    case "$(uname -m)" in
        s390*) echo cms ;;
    esac
    return 0
}

install() {
    # binaries we want in initramfs
    dracut_install eject -o pigz
    dracut_install depmod blkid
    inst_binary /usr/libexec/anaconda/dd_list /bin/dd_list
    inst_binary /usr/libexec/anaconda/dd_extract /bin/dd_extract

    # anaconda
    inst "$moddir/anaconda-lib.sh" "/lib/anaconda-lib.sh"
    inst_hook cmdline 25 "$moddir/parse-anaconda-options.sh"
    inst_hook cmdline 26 "$moddir/parse-anaconda-kickstart.sh"
    inst_hook cmdline 27 "$moddir/parse-anaconda-repo.sh"
    inst_hook cmdline 28 "$moddir/parse-anaconda-net.sh"
    inst_hook pre-udev 30 "$moddir/anaconda-modprobe.sh"
    inst_hook pre-trigger 50 "$moddir/repo-genrules.sh"
    inst_hook pre-trigger 50 "$moddir/kickstart-genrules.sh"
    inst_hook pre-trigger 50 "$moddir/updates-genrules.sh"
    inst_hook initqueue/settled 00 "$moddir/anaconda-ks-sendheaders.sh"
    inst_hook initqueue/online 80 "$moddir/anaconda-netroot.sh"
    inst "$moddir/anaconda-diskroot" "/sbin/anaconda-diskroot"
    inst_hook pre-pivot 50 "$moddir/anaconda-copy-ks.sh"
    inst_hook pre-pivot 50 "$moddir/anaconda-copy-cmdline.sh"
    inst_hook pre-pivot 99 "$moddir/save-initramfs.sh"
    inst_hook pre-shutdown 50 "$moddir/anaconda-pre-shutdown.sh"
    # kickstart parsing, WOOOO
    inst_hook initqueue/online 11 "$moddir/fetch-kickstart-net.sh"
    inst "$moddir/fetch-kickstart-disk" "/sbin/fetch-kickstart-disk"
    inst "$moddir/fetch-updates-disk" "/sbin/fetch-updates-disk"
    inst "$moddir/parse-kickstart" "/sbin/parse-kickstart"
    # Driver Update Disks
    inst_hook cmdline 29 "$moddir/parse-anaconda-dd.sh"
    inst_hook initqueue/online 10 "$moddir/fetch-driver-net.sh"
    inst_hook pre-trigger 40 "$moddir/driver-updates.sh"
    inst_hook pre-pivot 10 "$moddir/driver-updates-net.sh"
    inst_hook pre-pivot 50 "$moddir/anaconda-depmod.sh"
    inst "$moddir/driver-updates" "/bin/driver-updates"
    inst_simple "$moddir/driver-updates@.service" "/etc/systemd/system/driver-updates@.service"
    inst_simple "$moddir/driver-updates-net@.service" "/etc/systemd/system/driver-updates-net@.service"
    # python deps for parse-kickstart. DOUBLE WOOOO
    $moddir/python-deps $moddir/parse-kickstart $moddir/driver-updates | while read dep; do
        case "$dep" in
            *.so) inst_library $dep ;;
            *.py) inst_simple $dep ;;
            *) inst $dep ;;
        esac
    done
}

