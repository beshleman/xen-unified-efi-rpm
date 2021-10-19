%define with_test_signing 1

Summary: Xen is a virtual machine monitor
Name:    xen-unified
Version: 4.13.1
%define base_release 9.12.2
Release: %{base_release}%{?dist}
License: GPLv2 and LGPLv2+ and BSD
URL:     http://www.xenproject.org
Source0: %{name}-%{version}.tar
Source1: xen.cfg
%if %with_test_signing
Source2: test_certs.tar
%endif

%define efi_boot_entry xcp-ng-%{version}-%{base_release}-unified-no-grub

# Binutils 2.36 breaks xen.efi since both attempt to create reloc tables
# so it MUST 2.35 w/ the .buildid patch
BuildRequires: binutils == 2.35-5.xcpng8.2.2

# These packages MUST be the XCP-ng bespoke patched packages
BuildRequires: xen-hypervisor >= %{version}-%{base_release}.xcpng8.2
BuildRequires: kernel >= 4.19.19-7.0.9.1.xcpng8.2

Requires: efibootmgr

%if %with_test_signing
BuildRequires: sbsigntools

%package test-certs
Summary: The Test Certificates for the Unified EFI Xen Hypervisor
Requires: sbsigntools
%description test-certs


This package contains the test (NOT FOR PRODUCTION!) certificates for
the unified Xen EFI binary.
%endif

%define _kernel vmlinuz-4.19.0+1
%define xen_unified %{name}-%{version}-%{base_release}.unified.efi

%description
Xen, dom0 kernel, initrd and xen.cfg bundled into an EFI binary.

%prep
%autosetup -p1
%build

set -e

mkdir -p %{buildroot}/boot/efi/
OBJCOPY=objcopy
OBJDUMP=objdump

KERNEL=/boot/%{_kernel}
XEN=/boot/xen-%{version}-%{base_release}.efi

# Start at end of .pad section, see xen docs/misc/efi.pandoc
KERNEL_START=$(${OBJDUMP} -h ${XEN} | perl -ane '/\.pad/ && printf "0x%016x\n", hex($F[2]) + hex($F[3])')
KERNEL_SIZE=$(cat ${KERNEL} | wc -c)
KERNEL_END=$((${KERNEL_START} + ${KERNEL_SIZE}))

printf "kernel @ 0x%02lx - 0x%02lx\n" ${KERNEL_START} ${KERNEL_END}

${OBJCOPY}                                          \
	--add-section .kernel=${KERNEL}                 \
	--change-section-vma .kernel=${KERNEL_START}    \
	${XEN}                                          \
    %{xen_unified}

%if %with_test_signing

pushd %{_builddir}
tar xvf %{SOURCE2}
popd
certdir="%{_builddir}/test_certs/"
install -m 644 -d test_certs ${certdir}
KEY="${certdir}/test.key"
CERT="${certdir}/test.pem"
tmpfile="$(mktemp)"
sbsign --cert "${CERT}" --key "${KEY}" --output "${tmpfile}" %{xen_unified}
install -m 644 "${tmpfile}" %{xen_unified}
%endif

%install
mkdir -p %{buildroot}/boot/efi/EFI/xenserver/


cp %{_builddir}/%{name}-%{version}/%{name}-%{version}-%{base_release}.unified.efi \
    %{buildroot}/boot/efi/EFI/xenserver/%{name}-%{version}-%{base_release}.unified.efi

%if %with_test_signing
mkdir -p %{buildroot}/var/lib/secureboot/{keys,x509}

install -m 644 %{_builddir}/test_certs/test.der \
     %{buildroot}/boot/efi/EFI/xenserver/test.der

install -m 644 %{_builddir}/test_certs/test.key \
    %{buildroot}/var/lib/secureboot/x509/test.key

install -m 644 %{_builddir}/test_certs/test.der \
     %{buildroot}/var/lib/secureboot/x509/test.der

install -m 644 %{_builddir}/test_certs/test.pem \
     %{buildroot}/var/lib/secureboot/x509/test.pem

install -m 644 %{_builddir}/test_certs/db.auth \
     %{buildroot}/var/lib/secureboot/keys/db.auth

install -m 644 %{_builddir}/test_certs/PK.auth \
     %{buildroot}/var/lib/secureboot/keys/PK.auth

install -m 644 %{_builddir}/test_certs/KEK.auth \
     %{buildroot}/var/lib/secureboot/keys/KEK.auth

%endif

%post
cat > /boot/efi/EFI/xenserver/xen.cfg <<END
[global]
default=xcp-ng

[xcp-ng]
options=console=vga,com1 com1=115200,8n1 iommu=verbose ucode=scan flask=disabled vga=mode-0x0311 loglvl=all conring_size=2097152
kernel=vmlinuz-4.19-xen root=LABEL=$(basename /dev/disk/by-label/root-*) ro nolvm hpet=disable console=tty0 console=hvc0
ramdisk=initrd-4.19.0+1.img
END

diskpart=$(findmnt /boot/efi | grep \/boot\/efi | cut -d ' ' -f2)
disk=${diskpart//[0-9]/}
part=${diskpart//[^0-9]/}

efibootmgr \
    --create \
    --disk ${disk} \
    --part ${part} \
    --loader /EFI/xenserver/%{name}-%{version}-%{base_release}.unified.efi \
    --label "%{efi_boot_entry}" \
    --verbose

%postun
bootnum=$(efibootmgr | sed -n 's/^Boot\([0-9a-f]\{1,4\}\).*%{efi_boot_entry}$/\1/p')
efibootmgr --delete-bootnum --bootnum ${bootnum}

%if %with_test_signing
%post test-certs
sbkeysync --pk --verbose --keystore /var/lib/secureboot/keys/
%endif

%files
/boot/efi/EFI/xenserver/%{name}-%{version}-%{base_release}.unified.efi

%if %with_test_signing
%files test-certs
/boot/efi/EFI/xenserver/test.der
/var/lib/secureboot/x509/test.pem
/var/lib/secureboot/x509/test.key
/var/lib/secureboot/x509/test.der
/var/lib/secureboot/keys/db.auth
/var/lib/secureboot/keys/PK.auth
/var/lib/secureboot/keys/KEK.auth
%endif

%changelog
* Thu May 13 2021 Bobby Eshleman <bobby.eshleman@gmail.com> - 4.13.1-9.9.1
- Init commit
- Support xen.unified.efi
