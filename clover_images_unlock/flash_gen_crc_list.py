#!/usr/bin/env python
from __future__ import print_function
import getopt, posixpath, signal, struct, sys
import os
import binascii

sparse_file_list = {
	"system":"system.img",
	"cache":"cache.img",
	"persist":"persist.img",
	"cust":"cust.img",
	"userdata":"userdata.img",
}

unsparse_file_list = {
        "modem":"NON-HLOS.bin",
        "fsc":"zeros_1sector.bin",
        "sbl1":"sbl1.mbn",
        "sbl1bak":"sbl1.mbn",
        "rpm":"rpm.mbn",
        "rpmbak":"rpm.mbn",
        "tz":"tz.mbn",
        "tzbak":"tz.mbn",
        "devcfg":"devcfg.mbn",
        "devcfgbak":"devcfg.mbn",
        "dsp":"adspso.bin",
        "modemst1":"st1",
        "modemst2":"st2",
        "DDR":"zeros_1sector.bin",
        "fsg":"fs_image.tar.gz.mbn.img",
        "sec":"sec.dat",
        "splash":"splash.img",
        "aboot":"emmc_appsboot.mbn",
        "abootbak":"emmc_appsboot.mbn",
        "boot":"boot.img",
        "recovery":"recovery.img",
        "misc":"misc.img",
        "lksecapp":"lksecapp.mbn",
        "lksecappbak":"lksecapp.mbn",
        "cmnlib":"cmnlib.mbn",
        "cmnlibbak":"cmnlib.mbn",
        "cmnlib64":"cmnlib64.mbn",
        "cmnlib64bak":"cmnlib64.mbn",
        "keymaster":"keymaster.mbn",
        "keymasterbak":"keymaster.mbn",
        "apdp":"dp_AP_signed.mbn",
        "msadp":"dp_MSA_signed.mbn",
}

file_list=dict(unsparse_file_list,**sparse_file_list)

def gen_sparse_crc(path):
    FH = open(path, 'rb')
    header_bin = FH.read(28)
    header = struct.unpack("<I4H4I", header_bin)

    magic = header[0]
    major_version = header[1]
    minor_version = header[2]
    file_hdr_sz = header[3]
    chunk_hdr_sz = header[4]
    blk_sz = header[5]
    total_blks = header[6]
    total_chunks = header[7]
    image_checksum = header[8]
    sparsecrc=0

    if magic != 0xED26FF3A:
      print("%s: Magic should be 0xED26FF3A but is 0x%08X"
            % (path, magic))
      return 0
    if major_version != 1 or minor_version != 0:
      print("%s: I only know about version 1.0, but this is version %u.%u"
            % (path, major_version, minor_version))
      return 0
    if file_hdr_sz != 28:
      print("%s: The file header size was expected to be 28, but is %u."
            % (path, file_hdr_sz))
      return 0
    if chunk_hdr_sz != 12:
      print("%s: The chunk header size was expected to be 12, but is %u."
            % (path, chunk_hdr_sz))
      return 0

    print("%s: Total of %u %u-byte output blocks in %u input chunks."
          % (path, total_blks, blk_sz, total_chunks))

    if image_checksum != 0:
      print("checksum=0x%08X" % (image_checksum))

    offset = 0
    for i in xrange(1,total_chunks+1):
      header_bin = FH.read(12)
      header = struct.unpack("<2H2I", header_bin)
      chunk_type = header[0]
      reserved1 = header[1]
      chunk_sz = header[2]
      total_sz = header[3]
      data_sz = total_sz - 12

      if chunk_type == 0xCAC1:
        if data_sz != (chunk_sz * blk_sz):
          print("Raw chunk input size (%u) does not match output size (%u)"
                % (data_sz, chunk_sz * blk_sz))
          break;
        else:
          sparsecrc=binascii.crc32(FH.read(data_sz),sparsecrc)
      elif chunk_type == 0xCAC2:
        if data_sz != 4:
          print("Fill chunk should have 4 bytes of fill, but this has %u"
                % (data_sz), end="")
          break;
        else:
          fill_bin = FH.read(4)
          fill = struct.unpack("<I", fill_bin)
          print("Fill with 0x%08X" % (fill))
          fill_buf = [fill]*(blk_sz/data_sz)
          for j in xrange(1,chunk_sz+1):
            sparsecrc=binascii.crc32(fill_buf,sparsecrc)
      elif chunk_type == 0xCAC3:
        if data_sz != 0:
          print("Don't care chunk input size is non-zero (%u)" % (data_sz))
          break;
      elif chunk_type == 0xCAC4:
        if data_sz != 4:
          print("CRC32 chunk should have 4 bytes of CRC, but this has %u"
                % (data_sz), end="")
          break;
        else:
          crc_bin = FH.read(4)
          crc = struct.unpack("<I", crc)
          print("Unverified CRC32 0x%08X" % (crc))
      else:
          print("Unknown chunk type 0x%04X" % (chunk_type), end="")
          break;

      offset += chunk_sz
    return sparsecrc

def gen_crc(file_path):
	f = open(file_path, "rb")
	crc = binascii.crc32(f.read())

	return crc

def get_sparse_count(cmd):
	line = os.popen(cmd, 'r').readline()
	if line[0]=='I' or line[0]=='i':
		return -1;
	return int(line)

#------------------------------------------------------------------------------
if __name__ == "__main__":
	thispath = os.path.dirname(__file__)
	path = os.path.join(thispath, 'images')
	crclist = os.path.join(path, 'crclist.txt')
	sparsecrclist = os.path.join(path, 'sparsecrclist.txt')
	max_download_size = 512*1024*1024;
	crc = 0
	try:
		fs = open(sparsecrclist, 'w')
		f  = open(crclist, 'w')
		fs.write("SPARSECRC-LIST\n")
		f.write("CRC-LIST\n")
		for ptn in file_list:
			filepath = os.path.join(path, file_list[ptn])
			print(filepath)
			if not os.path.isfile(filepath):
				print(filepath + ' doesn\'t exist, skip it')
				continue
			if unsparse_file_list.has_key(ptn):
				crc = gen_crc(filepath)
				if crc:
					f.write(ptn + ' ' + hex(crc & (2**32-1)) + '\n')
			else:
				size = os.path.getsize(filepath)
				if size < max_download_size:
					crc = gen_crc(filepath)
					if crc:
						f.write(ptn + ' ' + hex(crc & (2**32-1)) + '\n')
				else:
					# need get the sparsecount
					cmdarg = './flash_gen_resparsecount' + ' -S ' + str(max_download_size) + ' ' +  filepath
					cmd = os.path.join(thispath, cmdarg)
					count = get_sparse_count(cmd)
					if count>0:
						countstr = str(count)
						crc = gen_sparse_crc(filepath)
						if crc:
							fs.write(ptn + ' ' + hex(crc & (2**32-1)) + ' ' + countstr + '\n')
	except Exception, e:
		os.remove(crclist)
		os.remove(sparsecrclist)
		raise

