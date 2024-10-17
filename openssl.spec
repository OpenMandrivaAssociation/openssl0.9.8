%define maj 0.9.8
%define libname %mklibname openssl %{maj}

%if %mandriva_branch == Cooker
# Cooker
%define release 2
%else
# Old distros
%define subrel 1
%define release 1
%endif 

Summary:	Secure Sockets Layer communications libs & utils
Name:		openssl%{maj}
Version:	%{maj}x
Release:        %{release}
License:	BSD-like
Group:		System/Libraries
URL:		https://www.openssl.org/
Source0:	ftp://ftp.openssl.org/source/openssl-%{version}.tar.gz
Source1:	ftp://ftp.openssl.org/source/openssl-%{version}.tar.gz.asc
# (gb) 0.9.6b-5mdk: Limit available SSL ciphers to 128 bits
Patch0:		openssl-0.9.6b-mdkconfig.patch
# (fg) 20010202 Patch from RH: some funcs now implemented with ia64 asm
Patch1:		openssl-0.9.7-ia64-asm.patch
# (gb) 0.9.7b-4mdk: Handle RPM_OPT_FLAGS in Configure
Patch2:		openssl-optflags.diff
# (gb) 0.9.7b-4mdk: Make it lib64 aware. TODO: detect in Configure
Patch3:		openssl-0.9.8b-lib64.diff
# (oe) support Brazilian Government OTHERNAME X509v3 field (#14158)
# http://www.iti.gov.br/resolucoes/RESOLU__O_13_DE_26_04_2002.PDF
Patch6:		openssl-0.9.8-beta6-icpbrasil.diff
Patch7:		openssl-0.9.8a-defaults.patch
Patch8:		openssl-0.9.8a-link-krb5.patch
Patch9:		openssl-0.9.8a-enginesdir.patch
Patch10:	openssl-0.9.7-beta6-ia64.patch
Patch12:	openssl-0.9.6-x509.patch
Patch13:	openssl-0.9.7-beta5-version-add-engines.patch
# http://qa.mandriva.com/show_bug.cgi?id=32621
Patch15:        openssl-0.9.8e-crt.patch
# http://blogs.sun.com/janp/
Patch16:	pkcs11_engine-0.9.8i.diff
# MIPS and ARM support
Patch300:	openssl-0.9.8-mips.patch
Patch301:	openssl-0.9.8-arm.patch
BuildRequires:	chrpath
BuildRequires:	zlib-devel
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
The openssl certificate management tool and the shared libraries that provide
various encryption and decription algorithms and protocols, including DES, RC4,
RSA and SSL.

NOTE: Only the shared library and the engines are provided with this source
rpm package.

%package -n	%{libname}
Summary:	Secure Sockets Layer communications libs
Group:		System/Libraries

%description -n	%{libname}
The libraries files are needed for various cryptographic algorithms
and protocols, including DES, RC4, RSA and SSL.

%prep

%setup -q -n openssl-%{version}
%patch1 -p1 -b .ia64-asm
%patch2 -p0 -b .optflags
%patch3 -p1 -b .lib64
%patch6 -p0 -b .icpbrasil
%patch7 -p1 -b .defaults
%patch9 -p0 -b .enginesdir
%patch10 -p0 -b .ia64
%patch12 -p1 -b .x509
%patch13 -p1 -b .version-add-engines
%patch15 -p1 -b .crt
%patch16 -p1 -b .pkcs11_engine

%patch300 -p0 -b .mips
%patch301 -p0 -b .arm

perl -pi -e "s,^(OPENSSL_LIBNAME=).+$,\1%{_lib}," Makefile.org engines/Makefile

# fix perl path
perl util/perlpath.pl %{_bindir}/perl

%build 
%serverbuild

# Figure out which flags we want to use.
# default
sslarch=%{_os}-%{_arch}
%ifarch %ix86
sslarch=linux-elf
if ! echo %{_target} | grep -q i[56]86 ; then
    sslflags="no-asm"
fi
%endif
%ifarch sparcv9
sslarch=linux-sparcv9
%endif
%ifarch alpha
sslarch=linux-alpha-gcc
%endif
%ifarch s390
sslarch="linux-generic32 -DB_ENDIAN -DNO_ASM"
%endif
%ifarch s390x
sslarch="linux-generic64 -DB_ENDIAN -DNO_ASM"
%endif

# ia64, x86_64, ppc, ppc64 are OK by default
# Configure the build tree.  Override OpenSSL defaults with known-good defaults
# usable on all platforms.  The Configure script already knows to use -fPIC and
# RPM_OPT_FLAGS, so we can skip specifiying them here.
./Configure \
    --prefix=%{_prefix} --openssldir=%{_sysconfdir}/pki/tls ${sslflags} \
    --enginesdir=%{_libdir}/openssl-%{maj}/engines \
     no-idea no-rc5 enable-camellia shared enable-tlsext ${sslarch} --pk11-libname=%{_libdir}/pkcs11/PKCS11_API.so

#    zlib no-idea no-mdc2 no-rc5 no-ec no-ecdh no-ecdsa shared ${sslarch}

# antibork stuff...
perl -pi -e "s|^#define ENGINESDIR .*|#define ENGINESDIR \"%{_libdir}/openssl-%{maj}/engines\"|g" crypto/opensslconf.h

# Add -Wa,--noexecstack here so that libcrypto's assembler modules will be
# marked as not requiring an executable stack.
RPM_OPT_FLAGS="%{optflags} -Wa,--noexecstack"
make depend
make all build-shared

# Generate hashes for the included certs.
make rehash build-shared

%install
rm -fr %{buildroot}

%makeinstall \
    INSTALL_PREFIX=%{buildroot} \
    MANDIR=%{_mandir} \
    build-shared

# the makefiles are too borked...
install -d %{buildroot}%{_libdir}/openssl-%{maj}
mv %{buildroot}%{_libdir}/engines %{buildroot}%{_libdir}/openssl-%{maj}/

# strip cannot touch these unless 755
chmod 755 %{buildroot}%{_libdir}/openssl-%{maj}/engines/*.so*
chmod 755 %{buildroot}%{_libdir}/*.so*

# nuke what we don't need
rm -rf %{buildroot}%{_sysconfdir}
rm -rf %{buildroot}%{_bindir}
rm -rf %{buildroot}%{_mandir}
rm -rf %{buildroot}%{_libdir}/pkgconfig
rm -rf %{buildroot}%{_includedir}
rm -f %{buildroot}%{_libdir}/lib*.so
rm -f %{buildroot}%{_libdir}/lib*.a

%clean
rm -fr %{buildroot}

%files -n %{libname}
%defattr(-,root,root)
%doc FAQ INSTALL LICENSE NEWS PROBLEMS README*
%attr(0755,root,root) %{_libdir}/lib*.so.*
%attr(0755,root,root) %dir %{_libdir}/openssl-%{maj}/engines
%attr(0755,root,root) %{_libdir}/openssl-%{maj}/engines/*.so


%changelog
* Fri May 11 2012 Oden Eriksson <oeriksson@mandriva.com> 0.9.8x-1mdv2012.0
+ Revision: 798208
- 0.9.8x

* Tue Apr 24 2012 Oden Eriksson <oeriksson@mandriva.com> 0.9.8w-1
+ Revision: 793114
- 0.9.8w

* Tue Mar 13 2012 Oden Eriksson <oeriksson@mandriva.com> 0.9.8u-1
+ Revision: 784666
- 0.9.8u

* Thu Jan 19 2012 Oden Eriksson <oeriksson@mandriva.com> 0.9.8t-1
+ Revision: 762529
- 0.9.8t

* Thu Oct 20 2011 Oden Eriksson <oeriksson@mandriva.com> 0.9.8r-2
+ Revision: 705506
- fix bork
- import openssl0.9.8


* Tue Oct 18 2011 Oden Eriksson <oeriksson@mandriva.com> 0.9.8r-1mdv2010.2
- initial Mandriva package
