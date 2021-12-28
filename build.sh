#!/bin/bash

XEN_VERSION="$(rpm -q xen-hypervisor | sed -e 's/xen-hypervisor-\(.*\)\.xcpng.*/\1/g' | cut -d '-' -f1)"
XEN_RELEASE="$(rpm -q xen-hypervisor | sed -e 's/xen-hypervisor-\(.*\)\.xcpng.*/\1/g' | cut -d '-' -f2)"

rpmbuild -ba SPECS/xen-unified-efi.spec --define "xen_release $XEN_RELEASE" --define "xen_version $XEN_VERSION"
