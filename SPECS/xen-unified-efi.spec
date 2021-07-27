Summary: Xen is a virtual machine monitor
Name:    xen-unified
Version: 4.13.1
%define base_release 9.10.2
Release: %{base_release}%{?dist}
License: GPLv2 and LGPLv2+ and BSD
URL:     http://www.xenproject.org
Source0: %{name}-%{version}.tar.gz
Source1: xen.cfg

BuildRequires: binutils
BuildRequires: xen-hypervisor >= %{version}-%{base_release}
BuildRequires: kernel >= 4.19.19-7.0.9.1

%define _initrd initrd-4.19.0+1.img
%define _kernel vmlinuz-4.19.0+1
%define _unified_xen 

%description
Xen, dom0 kernel, initrd and xen.cfg bundled into an EFI binary.

%prep
%autosetup -p1
%build

mkdir -p %{buildroot}/boot/efi/

# Round up x to nearest 8KB (0x2000).  8KB is arbitrary, the only thing that
# matters is that the sections don't overlap.
round_nearest_8kb() {
    local x=$1
    printf "0x%02lx" $((($x + (4096*2)) & ~(4096-1)))
}

CONFIG=%{buildroot}/boot/efi/xen.cfg
cat >> ${CONFIG} <<END
[global]
default=xcp-ng

[xcp-ng]
options=console=vga,com1 com1=115200,8n1 iommu=verbose ucode=scan flask=disabled vga=mode-0x0311 loglvl=all conring_size=2097152
kernel=%{_kernel} root=LABEL=root-hlexln ro nolvm hpet=disable console=tty0 console=hvc0
ramdisk=%{_initrd}
END

KERNEL=/boot/%{_kernel}
XEN=/boot/efi/xen-%{version}-%{base_release}.efi

# Start at end of .pad section, see xen docs/misc/efi.pandoc
CONFIG_START=$(objdump -h ${XEN} | perl -ane '/\.pad/ && printf "0x%016x\n", hex($F[2]) + hex($F[3])')
CONFIG_SIZE=$(cat ${CONFIG} | wc -c)
CONFIG_END=$((${CONFIG_START} + ${CONFIG_SIZE}))
KERNEL_START=$(round_nearest_8kb ${CONFIG_END})
KERNEL_SIZE=$(cat ${KERNEL} | wc -c)
KERNEL_END=$((${KERNEL_START} + ${KERNEL_SIZE}))

printf "config @ 0x%02lx - 0x%02lx\n" ${CONFIG_START} ${CONFIG_END}
printf "kernel @ 0x%02lx - 0x%02lx\n" ${KERNEL_START} ${KERNEL_END}

objcopy                                             \
	--add-section .config=${CONFIG}                 \
	--change-section-vma .config=${CONFIG_START}    \
	--add-section .kernel=${KERNEL}                 \
	--change-section-vma .kernel=${KERNEL_START}    \
	${XEN}                                          \
    %{name}-%{version}-%{base_release}.efi

%install
mkdir -p %{buildroot}/boot/efi/EFI/xenserver/

cp /boot/%{_initrd} %{buildroot}/boot/efi/EFI/xenserver/%{_initrd}
cp %{_builddir}/%{name}-%{version}/%{name}-%{version}-%{base_release}.efi \
    %{buildroot}/boot/efi/EFI/xenserver/%{name}-%{version}-%{base_release}.efi

%files
/boot/efi/EFI/xenserver/%{name}-%{version}-%{base_release}.efi
/boot/efi/EFI/xenserver/%{_initrd}

%changelog
* Thu May 13 2021 Bobby Eshleman <bobby.eshleman@gmail.com> - 4.13.1-9.9.1
- Init commit
- Support xen.unified.efi
