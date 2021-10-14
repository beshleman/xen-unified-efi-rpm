%define with_test_signing 1

Summary: Xen is a virtual machine monitor
Name:    xen-unified
Version: 4.13.1
%define base_release 9.10.2
Release: %{base_release}%{?dist}
License: GPLv2 and LGPLv2+ and BSD
URL:     http://www.xenproject.org
Source0: %{name}-%{version}.tar.gz
Source1: xen.cfg
%if %with_test_signing
Source2: test_certs.tar
%endif

BuildRequires: binutils
BuildRequires: xen-hypervisor >= %{version}-%{base_release}
BuildRequires: kernel >= 4.19.19-7.0.9.1

%if %with_test_signing
BuildRequires: pesign
BuildRequires: openssl
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

KERNEL=/boot/%{_kernel}
XEN=/boot/xen-%{version}-%{base_release}.efi

# Start at end of .pad section, see xen docs/misc/efi.pandoc
KERNEL_START=$(objdump -h ${XEN} | perl -ane '/\.pad/ && printf "0x%016x\n", hex($F[2]) + hex($F[3])')
KERNEL_SIZE=$(cat ${KERNEL} | wc -c)
KERNEL_END=$((${KERNEL_START} + ${KERNEL_SIZE}))

printf "kernel @ 0x%02lx - 0x%02lx\n" ${KERNEL_START} ${KERNEL_END}

objcopy                                             \
	--add-section .kernel=${KERNEL}                 \
	--change-section-vma .kernel=${KERNEL_START}    \
	${XEN}                                          \
    %{xen_unified}

%if %with_test_signing

tar xvf %{SOURCE2}

CA_NICK="Vates Test CA"
SIGNER_NICK="Vates Test"

certdir=test_certs/
certutil -d "${certdir}" -N
certutil -d "${certdir}" -L -n "${CA_NICK}" -r > ca.der

tmpfile=$(mktemp)

pesign                              \
    -s                              \
    -i "%{xen_unified}"             \
    -o "${tmpfile}"                 \
    -a                              \
    -c "${SIGNER_NICK}"             \
    -n "${certdir}"

install -m 644 ${tmpfile} %{xen_unified}
%endif

%install
mkdir -p %{buildroot}/boot/efi/EFI/xenserver/

cp %{_builddir}/%{name}-%{version}/%{name}-%{version}-%{base_release}.efi \
    %{buildroot}/boot/efi/EFI/xenserver/%{name}-%{version}-%{base_release}.efi

cat > /boot/efi/EFI/xenserver/xen.cfg <<END
[global]
default=xcp-ng

[xcp-ng]
options=console=vga,com1 com1=115200,8n1 iommu=verbose ucode=scan flask=disabled vga=mode-0x0311 loglvl=all conring_size=2097152
kernel=vmlinuz-4.19-xen root=LABEL=$(basename /dev/disk/by-label/root-*) ro nolvm hpet=disable console=tty0 console=hvc0
ramdisk=initrd-4.19.0+1.img
END

%files
/boot/efi/EFI/xenserver/%{name}-%{version}-%{base_release}.unified.efi

%changelog
* Thu May 13 2021 Bobby Eshleman <bobby.eshleman@gmail.com> - 4.13.1-9.9.1
- Init commit
- Support xen.unified.efi
