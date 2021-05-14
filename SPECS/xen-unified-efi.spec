Summary: Xen is a virtual machine monitor
Name:    xen-unified-efi
Version: 4.13.1
%define base_release 9.10.2
Release: %{base_release}%{?dist}
License: GPLv2 and LGPLv2+ and BSD
URL:     http://www.xenproject.org
Source0: xen-unified-efi-%{version}.tar.gz
Source1: xen.cfg

BuildRequires: binutils
BuildRequires: xen-hypervisor >= %{version}-%{base_release}
BuildRequires: kernel >= 4.19.19-7.0.9.1

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

find /boot/

CONFIG=%{SOURCE1}
KERNEL=/boot/vmlinuz-4.19.0+1
INITRD=/boot/initrd-4.19.0+1.img
XEN=/boot/efi/xen-%{version}-%{base_release}.efi

# Start at end of .pad section, see xen docs/misc/efi.pandoc
CONFIG_START=$(objdump -h ${XEN} | perl -ane '/\.pad/ && printf "0x%016x\n", hex($F[2]) + hex($F[3])')
CONFIG_SIZE=$(cat ${CONFIG} | wc -c)
CONFIG_END=$((${CONFIG_START} + ${CONFIG_SIZE}))
KERNEL_START=$(round_nearest_8kb ${CONFIG_END})
KERNEL_SIZE=$(cat ${KERNEL} | wc -c)
KERNEL_END=$((${KERNEL_START} + ${KERNEL_SIZE}))
INITRD_START=$(round_nearest_8kb ${KERNEL_END})
INITRD_SIZE=$(cat ${INITRD} | wc -c)
INITRD_END=$((${KERNEL_START} + ${INITRD_SIZE}))

printf "config @ 0x%02lx - 0x%02lx\n" ${CONFIG_START} ${CONFIG_END}
printf "kernel @ 0x%02lx - 0x%02lx\n" ${KERNEL_START} ${KERNEL_END}
printf "initrd @ 0x%02lx - 0x%02lx\n" ${INITRD_START} ${INITRD_END}

objcopy                                             \
	--add-section .config=${CONFIG}                 \
	--change-section-vma .config=${CONFIG_START}    \
	--add-section .kernel=${KERNEL}                 \
	--change-section-vma .kernel=${KERNEL_START}    \
	--add-section .ramdisk=${INITRD}                \
	--change-section-vma .ramdisk=${INITRD_START}   \
	${XEN}                                          \
	%{buildroot}/boot/efi/xen.unified.efi

%install

cp %{SOURCE1} %{buildroot}/boot/efi/xen.cfg

cp /boot/efi/xen-%{version}-%{base_release}.efi %{buildroot}/boot/efi/%{name}-%{version}-%{base_release}.unified.efi

%files
# For EFI
/boot/efi/%{name}-%{version}-%{base_release}.unified.efi
/boot/efi/xen.cfg

%changelog
* Thu May 13 2021 Bobby Eshleman <bobby.eshleman@gmail.com> - 4.13.1-9.9.1
- Init commit
- Support xen.unified.efi
