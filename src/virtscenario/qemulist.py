# Authors: Antoine Ginies <aginies@suse.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Qemu list of options, other VAR and qemu help
"""

OVMF_PATH = "/usr/share/qemu"
OVMF_VARS = "/var/lib/libvirt/qemu/nvram"

# qemu-system-x86_64 -machine help
LIST_MACHINETYPE = ['microvm', 'xenfv-4.2', 'xenfv', 'xenfv-3.1', 'pc', 'pc-i440fx-6.2',
                    'pc-i440fx-6.1', 'pc-i440fx-6.0', 'pc-i440fx-5.2', 'pc-i440fx-5.1',
                    'pc-i440fx-5.0', 'pc-i440fx-4.2', 'pc-i440fx-4.1', 'pc-i440fx-4.0',
                    'pc-i440fx-3.1', 'pc-i440fx-3.0', 'pc-i440fx-2.9', 'pc-i440fx-2.8',
                    'pc-i440fx-2.7', 'pc-i440fx-2.6', 'pc-i440fx-2.5', 'pc-i440fx-2.4',
                    'pc-i440fx-2.3', 'pc-i440fx-2.2', 'pc-i440fx-2.12', 'pc-i440fx-2.11',
                    'pc-i440fx-2.10', 'pc-i440fx-2.1', 'pc-i440fx-2.0', 'pc-i440fx-1.7',
                    'pc-i440fx-1.6', 'pc-i440fx-1.5', 'pc-i440fx-1.4', 'q35', 'pc-q35-6.2',
                    'pc-q35-6.1', 'pc-q35-6.0', 'pc-q35-5.2', 'pc-q35-5.1', 'pc-q35-5.0',
                    'pc-q35-4.2', 'pc-q35-4.1', 'pc-q35-4.0.1', 'pc-q35-4.0', 'pc-q35-3.1',
                    'pc-q35-3.0', 'pc-q35-2.9', 'pc-q35-2.8', 'pc-q35-2.7', 'pc-q35-2.6',
                    'pc-q35-2.5', 'pc-q35-2.4', 'pc-q35-2.12', 'pc-q35-2.11', 'pc-q35-2.10',
                    'isapc']

LIST_BOOTDEV = ['hd', 'cdrom', 'floppy', 'network']

DISK_CACHE = ['none', 'writeback', 'writethrough', 'unsafe', 'directsync']

DISK_FORMAT = ['qcow2', 'raw']

PRE_ALLOCATION = ['off', 'metadata', 'falloc', 'full']

##
CLUSTER_SIZE = "cluster_size:\nChanges the qcow2 cluster size (must be between 512 and 2M). Smaller cluster sizes can improve the image file size whereas larger cluster sizes generally provide better performance.\n"

PREALLOCATION ="preallocation:\nPreallocation mode (allowed values: off, metadata, falloc, full). An image with preallocated metadata is initially larger but can improve performance when the image needs to grow. falloc and full preallocations are like the same options of raw format, but sets up metadata also.\n"

LAZY_REFCOUNTS ="lazy_refcounts:\nIf this option is set to on, reference count updates are postponed with the goal of avoiding metadata I/O and improving performance. This is particularly interesting with cache=writethrough which doesn’t batch metadata updates. The tradeoff is that after a host crash, the reference count tables must be rebuilt (qemu-img check -r all is required).\n"

## https://documentation.suse.com/sles/15-SP4/html/SLES-all/cha-cachemodes.html#cachemodes-descr
WRITEBACK = "<b>writeback</b>\nwriteback uses the host page cache. Writes are reported to the guest as completed when they are placed in the host cache. Cache management handles commitment to the storage device. The guest's virtual storage adapter is informed of the writeback cache and therefore expected to send flush commands as needed to manage data integrity.\n\n"

WRITETHROUGH = "<b>writethrough</b>\nWrites are reported as completed only when the data has been committed to the storage device. The guest's virtual storage adapter is informed that there is no writeback cache, so the guest does not need to send flush commands to manage data integrity.\n\n"

NONE = "<b>none</b>\nThe host cache is bypassed, and reads and writes happen directly between the hypervisor and the storage device. This mode is equivalent to direct access to the host's disk.\n\n"

UNSAFE = "<b>unsafe</b>\nSimilar to the writeback mode, except all flush commands from the guests are ignored. Using this mode implies that the user prioritizes performance gain over the risk of data loss in case of a host failure. This mode can be useful during guest installation, but not for production workloads.\n\n"

DIRECTSYNC = "<b>directsync</b>\nWrites are reported as completed only when the data has been committed to the storage device and the host cache is bypassed. This mode can be useful for guests that do not send flushes when needed.\n"

STORAGE_HELP = "\n<u>Disk Cache Options</u>\n"+WRITEBACK+WRITETHROUGH+NONE+UNSAFE+DIRECTSYNC

QCOW2 = "QCOW2:\nThe most versatile format. Use it to have smaller images (useful if your  filesystem does not supports holes, for example on Windows), optional AES encryption, zlib based compression and support of multiple VM snapshots"

RAW = "RAW:\nThis format has the advantage of being simple and easily exportable to all other emulators. If your file system supports holes (for example in ext2 or ext3 on  Linux or NTFS  on  Windows), then  only the written sectors will reserve space."

IMAGE_FORMAT=QCOW2+"\n\n"+RAW
