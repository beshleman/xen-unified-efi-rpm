RPM sources for the xen-unified package in XCP-ng (https://xcp-ng.org/).

Make sure to have `git-lfs` installed before cloning. It is used for handling source archives separately.

Branches:
* `master` contains sources for the next `x.y` release of XCP-ng.
* `x.y` (e.g. `7.5`) contains sources for the `x.y` release of XCP-ng, with their bugfix and/or security updates.
* `XS-x.y` (e.g. `XS-7.5`), when they exist, contain sources from the `x.y` release of XenServer, with trademarked or copyrighted material stripped if needed.

Built RPMs and source RPMs are available on https://updates.xcp-ng.org.

## Overview

In order to support a shim-less Secure Boot boot chain in XCP-ng, we've set out
to support the boot mechanism in upstream Xen known as the unified Xen
image[^1]. The unified Xen image can consist of many things, but should *at
least*[^2] consist of these two:

1. The Xen EFI image
2. The dom0 kernel *embedded into* the Xen EFI image.

Upstream Xen knows to search a specific section in the EFI image for the kernel
when it has been booted as an EFI image.

This enables distributions, like XCP-ng, to sign Xen *and* the kernel as a
single image. When Xen is varied by the Secure Boot enabled UEFI bootloader,
both the kernel and Xen will be verified.

## Why not just use Xen.efi and a separate kernel?

The Xen EFI image does support the ability to measure kernels that are not
embedded into it using the unified image technique. This, however, requires
that `shim` was used as an intermediary bootloader. It has been explicitly
requested that shim be omitted from our bootchain by users, so this is not a
feasible route.

## Requirements

In order to support a shim-less Secure Boot boot chain, the following things
are required (checked items done):

- [x] Patch Xen to understand the unified boot technique (extracting the kernel
      from itself)
- [x] Create an RPM to that takes the Xen EFI image and the XCP-ng dom0 kernel
      and bundles it into an EFI image.
      https://github.com/beshleman/xen-rpm/tree/xen-unified-v2.
- [x] Support the usage of test certificates for signing the binary and deploying
      it to a test system. Found in the current repo.
- [x] The correctly patched binutils to both build the EFI image *and* create the
      unified image. https://github.com/beshleman/binutils-rpm/tree/xcp-ng-8.2-efi
- [x] A signing utility bundled for XCP-ng (in this case, sbsigntools as been prepared)
      https://github.com/beshleman/sbsigntools-rpm
- [ ] Support the automated build and release of the *signed* unified image.

## The `xen-unified-test-certs` RPM

The RPM entitled xen-unified-test-certs attempts to install the set of test certificates
onto the test system. The certificates are stored into the directory /var/lib/secureboot/.
It also attempts to install them into the EFI firmware using the tool `sbkeysync`, but
it doesn't seem to want to install the PK.

### Installing the PK

If `xen-unified-test-certs` fails to install the PK, it may be installed manually.

1. Copy /var/lib/secureboots/x509/test.der to /boot/efi/ (or anywhere else
   in the ESP).
2. Reboot the machine into the UEFI shell, navigate to secure boot options, and
   enroll to the PK the test.der certificate.
3. Enable Secure Boot and reboot.

# Testing

After installing the RPM, the certificates, enabling Secure Boot in the UEFI menu,
and rebooting the machine, the dmesg output should yield the following:

```bash
$ dmesg | grep -i secure
[    0.000000] UEFI Secure Boot is enabled.
[    0.705567] Secure boot enabled
```

## Footnotes

[^1]: "image" refers to the EFI binary.
[^2]: "at least" refers to making XCP-ng's boot chain security guarantees
      competitive with a typical Linux distribution.
