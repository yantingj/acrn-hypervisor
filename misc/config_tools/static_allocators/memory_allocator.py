#!/usr/bin/env python3
#
# Copyright (C) 2022 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#

import os
import sys
import lib.error
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'library'))
import common

def import_memory_info(board_etree):
    ram_range = {}
    start = board_etree.xpath("/acrn-config/memory/range/@start")
    size = board_etree.xpath("/acrn-config/memory/range/@size")
    for i in range(len(start)):
        start_hex = int(start[i], 16)
        size_hex = int(size[i], 10)
        ram_range[start_hex] = size_hex

    return ram_range

def check_hpa(vm_node_info):
    hpa_node_list = vm_node_info.xpath("./memory/hpa_region/*")
    hpa_node_list_new = []
    for hpa_node in hpa_node_list:
        if int(hpa_node.text, 16) != 0:
            hpa_node_list_new.append(hpa_node)

    return hpa_node_list_new

def get_memory_info(vm_node_info):
    start_hpa = []
    size_hpa = []
    hpa_info = {}

    whole_node_list = vm_node_info.xpath("./memory/size")
    if len(whole_node_list) != 0:
        hpa_info[0] = int(whole_node_list[0].text, 16)
    hpa_node_list = check_hpa(vm_node_info)
    if len(hpa_node_list) != 0:
        for hpa_node in hpa_node_list:
            if hpa_node.tag == "start_hpa":
                start_hpa.append(int(hpa_node.text, 16))
            elif hpa_node.tag == "size_hpa":
                size_hpa.append(int(hpa_node.text))
    if len(start_hpa) != 0 and len(start_hpa) == len(start_hpa):
        for i in range(len(start_hpa)):
            hpa_info[start_hpa[i]] = size_hpa[i]

    return hpa_info

def alloc_memory(scenario_etree, ram_range_info):
    vm_node_list = scenario_etree.xpath("/acrn-config/vm[load_order = 'PRE_LAUNCHED_VM']")
    mem_info_list = []
    vm_node_index_list = []
    dic_key = sorted(ram_range_info)
    for key in dic_key:
        if key <= 0x100000000:
            ram_range_info.pop(key)

    for vm_node in vm_node_list:
        mem_info = get_memory_info(vm_node)
        mem_info_list.append(mem_info)
        vm_node_index_list.append(vm_node.attrib["id"])

    ram_range_info = alloc_hpa_region(ram_range_info, mem_info_list, vm_node_index_list)
    ram_range_info, mem_info_list = alloc_whole_size(ram_range_info, mem_info_list, vm_node_index_list)

    return ram_range_info, mem_info_list, vm_node_index_list

def alloc_hpa_region(ram_range_info, mem_info_list, vm_node_index_list):
    mem_key = sorted(ram_range_info)
    for vm_index in range(len(vm_node_index_list)):
        hpa_key = sorted(mem_info_list[vm_index])
        for mem_start in mem_key:
            mem_size = ram_range_info[mem_start]
            for hpa_start in hpa_key:
                hpa_size = mem_info_list[vm_index][hpa_start]
                if hpa_start != 0:
                    if mem_start < hpa_start and mem_start + mem_size > hpa_start + hpa_size:
                        ram_range_info[mem_start] = hpa_start - mem_start
                        ram_range_info[hpa_start - mem_start] = mem_start + mem_size - hpa_start - hpa_size
                    elif mem_start == hpa_start and mem_start + mem_size > hpa_start + hpa_size:
                        del ram_range_info[mem_start]
                        ram_range_info[hpa_start + hpa_size] = mem_start + mem_size - hpa_start - hpa_size
                    elif mem_start < hpa_start and mem_start + mem_size == hpa_start + hpa_size:
                        ram_range_info[mem_start] = hpa_start - mem_start
                    elif mem_start == hpa_start and mem_start + mem_size == hpa_start + hpa_size:
                        del ram_range_info[mem_start]
                    elif mem_start > hpa_start or mem_start + mem_size < hpa_start + hpa_size:
                        raise lib.error.ResourceError(f"Start address of HPA is out of available memory range: vm id: {vm_index}, hpa_start: {hpa_start}.")
                    elif mem_size < hpa_size:
                        raise lib.error.ResourceError(f"Size of HPA is out of available memory range: vm id: {vm_index}, hpa_size: {hpa_size}.")

    return ram_range_info

def alloc_whole_size(ram_range_info, mem_info_list, vm_node_index_list):
    for vm_index in range(len(vm_node_index_list)):
        if 0 in mem_info_list[vm_index].keys() and mem_info_list[vm_index][0] != 0:
            remain_size = mem_info_list[vm_index][0]
            hpa_info = mem_info_list[vm_index]
            mem_key = sorted(ram_range_info)
            for mem_start in mem_key:
                mem_size = ram_range_info[mem_start]
                if remain_size != 0 and remain_size <= mem_size:
                    del ram_range_info[mem_start]
                    hpa_info[mem_start] = remain_size
                    del hpa_info[0]
                    if mem_size > remain_size:
                        ram_range_info[mem_start + remain_size] = mem_size - remain_size
                    remain_size = 0
                elif remain_size > mem_size:
                    hpa_info[mem_start] = mem_size
                    del ram_range_info[mem_start]
                    hpa_info[0] = remain_size - mem_size
                    remain_size = hpa_info[0]

    return ram_range_info, mem_info_list

def write_hpa_info(allocation_etree, mem_info_list, vm_node_index_list):
    for i in range(len(vm_node_index_list)):
        vm_id = vm_node_index_list[i]
        hpa_info = mem_info_list[i]
        vm_node = common.get_node(f"/acrn-config/vm[@id = '{vm_id}']", allocation_etree)
        if vm_node is None:
            vm_node = common.append_node("/acrn-config/vm", None, allocation_etree, id=vm_id)
        memory_node = common.get_node("./memory", vm_node)
        if memory_node is None:
            memory_node = common.append_node(f"./memory", None, vm_node)
        region_index = 1
        start_key = sorted(hpa_info)
        for start_hpa in start_key:
            hpa_region_node = common.get_node(f"./hpa_region[@id='{region_index}']", memory_node)
            if hpa_region_node is None:
                hpa_region_node = common.append_node("./hpa_region", None, memory_node, id=str(region_index).encode('UTF-8'))

                start_hpa_node = common.get_node("./start_hpa", hpa_region_node)
                if start_hpa_node is None:
                    common.append_node("./start_hpa", hex(start_hpa), hpa_region_node)

                size_hpa_node = common.get_node("./size_hpa", hpa_region_node)
                if size_hpa_node is None:
                    common.append_node("./size_hpa", hex(hpa_info[start_hpa] * 0x100000), hpa_region_node)
            region_index = region_index + 1

def alloc_vm_memory(board_etree, scenario_etree, allocation_etree):
    ram_range_info = import_memory_info(board_etree)
    ram_range_info, mem_info_list, vm_node_index_list = alloc_memory(scenario_etree, ram_range_info)
    write_hpa_info(allocation_etree, mem_info_list, vm_node_index_list)

def fn(board_etree, scenario_etree, allocation_etree):
    alloc_vm_memory(board_etree, scenario_etree, allocation_etree)
