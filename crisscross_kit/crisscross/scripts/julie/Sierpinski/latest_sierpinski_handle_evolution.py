#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure, get_slat_key

    corner_file = '/Users/juliefinkel/Documents/Projects_postdoc/CrissCross/Sierpinski_triangle_designs/Gadgets_design/Count_8/Sierpinski_core_with_dummy_slats.xlsx'

    megastructure = Megastructure(import_design_file=corner_file)

    # ---------- Linkers functions
    # L3 to L2                      
    def link_l3_to_l2_by_ranges(megastructure, l3_slat, l3_range, l2_slat, l2_range, linked_handles):
        """
        Link one L3 range to one L2 range, index-wise, inclusive. Enforces: one L3 handle -> at most one L2 handle.
        """
        slats = megastructure.slats
        get_key = get_slat_key
        coords3 = slats[get_key(3, l3_slat)].slat_position_to_coordinate
        coords2 = slats[get_key(2, l2_slat)].slat_position_to_coordinate
    
        L3 = list(range(l3_range[0], l3_range[1]+1))
        L2 = list(range(l2_range[0], l2_range[1]+1))
        if len(L3) != len(L2):
            raise ValueError(f"L3 len {len(L3)} != L2 len {len(L2)} for L3 slat {l3_slat}")
    
        for p3, p2 in zip(L3, L2):
            c3 = coords3[p3]
            c2 = coords2[p2]
            key_from = (3, 'bottom', c3)
            if key_from in linked_handles:
                existing = linked_handles[key_from]
                if isinstance(existing, list):
                    existing.append((2, 'top', c2))
                else:
                    linked_handles[key_from] = [existing, (2, 'top', c2)]
            else:
                linked_handles[key_from] = (2, 'top', c2)
    
    def merge_no_overwrite(dst: dict, src: dict):
        for key, value in src.items():
            if key in dst:
                existing = dst[key]
                if isinstance(existing, list):
                    if isinstance(value, list):
                        for v in value:
                            if v not in existing:
                                existing.append(v)
                    else:
                        if value not in existing:
                            existing.append(value)
                else:
                    merged = [existing]
                    if isinstance(value, list):
                        for v in value:
                            if v not in merged:
                                merged.append(v)
                    elif value not in merged:
                        merged.append(value)
                    dst[key] = merged
            else:
                dst[key] = value
    
    def build_l3_block_pairs(megastructure, l3_list, pair_list):
        """
        pair_list: [(l2_for_1to8, l2_for_9to32), ...] aligned with l3_list.
        """
        out = {}
        for l3, (l2a, l2b) in zip(l3_list, pair_list):
            link_l3_to_l2_by_ranges(megastructure, l3, (1,8),  l2a, (25,32), out)
            link_l3_to_l2_by_ranges(megastructure, l3, (9,32), l2b, (1,24),  out)
        return out
    
    # L3 -> L2
    seed_l3_pairs = [
        (16,(11,27)), #c
        (15,(8,24)),  #h
        (14,(5,21)),  #f
        (13,(2,18)),  #g
        (12,(9,25)),  #a
        (11,(16,32)), #c
        (10,(1,17)),  #b
        (9,(12,28)),  #a
        (8,(15,31)),  #h
        (7,(6,22)),   #e
        (6,(7,23)),   #e
        (5,(14,30)),  #f
        (4,(3,19)),   #d
        (3,(4,20)),   #d
        (2,(13,29)),  #g
        (1,(10,26)),  #b
    ]
    
    L3_to_L2_blocks = [
        #Seed
        ([x for x,_ in seed_l3_pairs],
         [y for _,y in seed_l3_pairs]),
        #G1
        ([17,18,19,20,21,22,23,24],
         [(44,45),(50,51),(54,55),(34,35),(48,49),(46,47),(36,37),(38,39)]),
        #G2
        ([40,39,38,37,36,35,34,33],
         [(124,125),(130,131),(134,135),(114,115),(128,129),(126,127),(116,117),(118,119)]),
        #G3
        ([56,55,54,53,52,51,50,49],
        [(174,175),(180,181),(184,185),(163,164),(178,179),(176,177),(165,166),(167,168)]),
        #R1
        ([25,26,27,28,29,30,31,32],
        [(64,65),(68,69),(57,58),(79,80),(62,63),(76,77),(74,75),(66,67)]),
        #R2
        ([41,42,43,44,45,46,47,48],
        [(145,146),(149,150),(138,139),(160,161),(143,144),(157,158),(155,156),(147,148)]),
        #R3
        ([57,58,59,60,61,62,63,64],
        [(199,200),(204,205),(192,193),(215,216),(197,198),(212,213),(210,211),(201,203)]),
    ]
                

    #L2 to L1 (Slat count 8)
    
    slat_count_c = { # For L1 index = 0 ; here the numbers 0, 1, 2, 4, 5, 8, 10 are the numbers to add to base_L1 to find the positions on L1
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 5},
            {"idx_L2_slat": 9, "idx_L2_pos": 5},
            {"idx_L2_slat": 9, "idx_L2_pos": 0},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 5},
            {"idx_L2_slat": 12, "idx_L2_pos": 5},
            {"idx_L2_slat": 12, "idx_L2_pos": 0},
        ],
    
        2: [
            {"idx_L2_slat": 2,  "idx_L2_pos": 5},
            {"idx_L2_slat": 3,  "idx_L2_pos": 5},
            {"idx_L2_slat": 3,  "idx_L2_pos": 0},
        ],
    
        4: [
            {"idx_L2_slat": 4,   "idx_L2_pos": 5},
            {"idx_L2_slat": 13,  "idx_L2_pos": 5},
            {"idx_L2_slat": 13,  "idx_L2_pos": 0},  
        ],
        5: [
            {"idx_L2_slat": 5,  "idx_L2_pos": 5},
            {"idx_L2_slat": 6,  "idx_L2_pos": 5},
            {"idx_L2_slat": 6,  "idx_L2_pos": 0},  
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 5},
            {"idx_L2_slat": 14,  "idx_L2_pos": 5},
            {"idx_L2_slat": 14,  "idx_L2_pos": 0},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 5},
            {"idx_L2_slat": 11,  "idx_L2_pos": 5},
            {"idx_L2_slat": 11,  "idx_L2_pos": 0},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 5},
            {"idx_L2_slat": 15,  "idx_L2_pos": 5},
            {"idx_L2_slat": 15,  "idx_L2_pos": 0},  
        ],
    }
    
    slat_count_h = { # For L1 index = 1
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 8},
            {"idx_L2_slat": 9, "idx_L2_pos": 8},
            {"idx_L2_slat": 9, "idx_L2_pos": 1},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 8},
            {"idx_L2_slat": 12, "idx_L2_pos": 8},
            {"idx_L2_slat": 12, "idx_L2_pos": 1},
        ],
    
        2: [
            {"idx_L2_slat": 2, "idx_L2_pos": 8},
            {"idx_L2_slat": 3, "idx_L2_pos": 8},
            {"idx_L2_slat": 3, "idx_L2_pos": 1},
        ],
    
        4: [
            {"idx_L2_slat": 4,  "idx_L2_pos": 8},
            {"idx_L2_slat": 13, "idx_L2_pos": 8},
            {"idx_L2_slat": 13, "idx_L2_pos": 1},
        ],
        5: [
            {"idx_L2_slat": 5, "idx_L2_pos": 8},
            {"idx_L2_slat": 6, "idx_L2_pos": 8},
            {"idx_L2_slat": 6, "idx_L2_pos": 1},
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 8},
            {"idx_L2_slat": 14,  "idx_L2_pos": 8},
            {"idx_L2_slat": 14,  "idx_L2_pos": 1},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 8},
            {"idx_L2_slat": 11,  "idx_L2_pos": 8},
            {"idx_L2_slat": 11,  "idx_L2_pos": 1},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 8},
            {"idx_L2_slat": 15,  "idx_L2_pos": 8},
            {"idx_L2_slat": 15,  "idx_L2_pos": 1},  
        ],
    }
    
    slat_count_f = { # For L1 index = 2
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 11},
            {"idx_L2_slat": 9, "idx_L2_pos": 11},
            {"idx_L2_slat": 9, "idx_L2_pos":  2},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 11},
            {"idx_L2_slat": 12, "idx_L2_pos": 11},
            {"idx_L2_slat": 12, "idx_L2_pos":  2},
        ],
    
        2: [
            {"idx_L2_slat": 2, "idx_L2_pos": 11},
            {"idx_L2_slat": 3, "idx_L2_pos": 11},
            {"idx_L2_slat": 3, "idx_L2_pos":  2},
        ],
    
        4: [
            {"idx_L2_slat": 4,  "idx_L2_pos": 11},
            {"idx_L2_slat": 13, "idx_L2_pos": 11},
            {"idx_L2_slat": 13, "idx_L2_pos":  2},
        ],
        5: [
            {"idx_L2_slat": 5, "idx_L2_pos": 11},
            {"idx_L2_slat": 6, "idx_L2_pos": 11},
            {"idx_L2_slat": 6, "idx_L2_pos":  2},
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 11},
            {"idx_L2_slat": 14,  "idx_L2_pos": 11},
            {"idx_L2_slat": 14,  "idx_L2_pos":  2},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 11},
            {"idx_L2_slat": 11,  "idx_L2_pos": 11},
            {"idx_L2_slat": 11,  "idx_L2_pos":  2},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 11},
            {"idx_L2_slat": 15,  "idx_L2_pos": 11},
            {"idx_L2_slat": 15,  "idx_L2_pos":  2},  
        ],
    }
    
    slat_count_g = { # For L1 index = 3
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 14},
            {"idx_L2_slat": 9, "idx_L2_pos": 14},
            {"idx_L2_slat": 9, "idx_L2_pos":  3},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 14},
            {"idx_L2_slat": 12, "idx_L2_pos": 14},
            {"idx_L2_slat": 12, "idx_L2_pos":  3},
        ],
    
        2: [
            {"idx_L2_slat": 2, "idx_L2_pos": 14},
            {"idx_L2_slat": 3, "idx_L2_pos": 14},
            {"idx_L2_slat": 3, "idx_L2_pos":  3},
        ],
    
        4: [
            {"idx_L2_slat": 4,  "idx_L2_pos": 14},
            {"idx_L2_slat": 13, "idx_L2_pos": 14},
            {"idx_L2_slat": 13, "idx_L2_pos":  3},
        ],
        5: [
            {"idx_L2_slat": 5, "idx_L2_pos": 14},
            {"idx_L2_slat": 6, "idx_L2_pos": 14},
            {"idx_L2_slat": 6, "idx_L2_pos":  3},
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 14},
            {"idx_L2_slat": 14,  "idx_L2_pos": 14},
            {"idx_L2_slat": 14,  "idx_L2_pos":  3},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 14},
            {"idx_L2_slat": 11,  "idx_L2_pos": 14},
            {"idx_L2_slat": 11,  "idx_L2_pos":  3},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 14},
            {"idx_L2_slat": 15,  "idx_L2_pos": 14},
            {"idx_L2_slat": 15,  "idx_L2_pos":  3},  
        ],
    }
    
    slat_count_a = { # For L1 index = 4
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 7},
            {"idx_L2_slat": 9, "idx_L2_pos": 7},
            {"idx_L2_slat": 9, "idx_L2_pos": 4},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 7},
            {"idx_L2_slat": 12, "idx_L2_pos": 7},
            {"idx_L2_slat": 12, "idx_L2_pos": 4},
        ],
    
        2: [
            {"idx_L2_slat": 2, "idx_L2_pos": 7},
            {"idx_L2_slat": 3, "idx_L2_pos": 7},
            {"idx_L2_slat": 3, "idx_L2_pos": 4},
        ],
    
        4: [
            {"idx_L2_slat": 4,  "idx_L2_pos": 7},
            {"idx_L2_slat": 13, "idx_L2_pos": 7},
            {"idx_L2_slat": 13, "idx_L2_pos": 4},
        ],
        5: [
            {"idx_L2_slat": 5, "idx_L2_pos": 7},
            {"idx_L2_slat": 6, "idx_L2_pos": 7},
            {"idx_L2_slat": 6, "idx_L2_pos": 4},
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 7},
            {"idx_L2_slat": 14,  "idx_L2_pos": 7},
            {"idx_L2_slat": 14,  "idx_L2_pos": 4},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 7},
            {"idx_L2_slat": 11,  "idx_L2_pos": 7},
            {"idx_L2_slat": 11,  "idx_L2_pos": 4},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 7},
            {"idx_L2_slat": 15,  "idx_L2_pos": 7},
            {"idx_L2_slat": 15,  "idx_L2_pos": 4},  
        ],
    }
    
    slat_count_b = { # For L1 index = 6
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 15},
            {"idx_L2_slat": 9, "idx_L2_pos": 15},
            {"idx_L2_slat": 9, "idx_L2_pos":  6},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 15},
            {"idx_L2_slat": 12, "idx_L2_pos": 15},
            {"idx_L2_slat": 12, "idx_L2_pos":  6},
        ],
    
        2: [
            {"idx_L2_slat": 2, "idx_L2_pos": 15},
            {"idx_L2_slat": 3, "idx_L2_pos": 15},
            {"idx_L2_slat": 3, "idx_L2_pos":  6},
        ],
    
        4: [
            {"idx_L2_slat": 4,  "idx_L2_pos": 15},
            {"idx_L2_slat": 13, "idx_L2_pos": 15},
            {"idx_L2_slat": 13, "idx_L2_pos":  6},
        ],
        5: [
            {"idx_L2_slat": 5, "idx_L2_pos": 15},
            {"idx_L2_slat": 6, "idx_L2_pos": 15},
            {"idx_L2_slat": 6, "idx_L2_pos":  6},
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 15},
            {"idx_L2_slat": 14,  "idx_L2_pos": 15},
            {"idx_L2_slat": 14,  "idx_L2_pos":  6},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 15},
            {"idx_L2_slat": 11,  "idx_L2_pos": 15},
            {"idx_L2_slat": 11,  "idx_L2_pos":  6},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 15},
            {"idx_L2_slat": 15,  "idx_L2_pos": 15},
            {"idx_L2_slat": 15,  "idx_L2_pos":  6},  
        ],
    }
    
    slat_count_e = { # For L1 index = 9
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 10},
            {"idx_L2_slat": 9, "idx_L2_pos": 10},
            {"idx_L2_slat": 9, "idx_L2_pos":  9},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 10},
            {"idx_L2_slat": 12, "idx_L2_pos": 10},
            {"idx_L2_slat": 12, "idx_L2_pos":  9},
        ],
    
        2: [
            {"idx_L2_slat": 2, "idx_L2_pos": 10},
            {"idx_L2_slat": 3, "idx_L2_pos": 10},
            {"idx_L2_slat": 3, "idx_L2_pos":  9},
        ],
    
        4: [
            {"idx_L2_slat": 4,  "idx_L2_pos": 10},
            {"idx_L2_slat": 13, "idx_L2_pos": 10},
            {"idx_L2_slat": 13, "idx_L2_pos":  9},
        ],
        5: [
            {"idx_L2_slat": 5, "idx_L2_pos": 10},
            {"idx_L2_slat": 6, "idx_L2_pos": 10},
            {"idx_L2_slat": 6, "idx_L2_pos":  9},
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 10},
            {"idx_L2_slat": 14,  "idx_L2_pos": 10},
            {"idx_L2_slat": 14,  "idx_L2_pos":  9},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 10},
            {"idx_L2_slat": 11,  "idx_L2_pos": 10},
            {"idx_L2_slat": 11,  "idx_L2_pos":  9},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 10},
            {"idx_L2_slat": 15,  "idx_L2_pos": 10},
            {"idx_L2_slat": 15,  "idx_L2_pos":  9},  
        ],
    }
    
    slat_count_d = { # For L1 index = 12
        0: [
            {"idx_L2_slat": 0, "idx_L2_pos": 13},
            {"idx_L2_slat": 9, "idx_L2_pos": 13},
            {"idx_L2_slat": 9, "idx_L2_pos": 12},
        ],
    
        1: [
            {"idx_L2_slat": 1,  "idx_L2_pos": 13},
            {"idx_L2_slat": 12, "idx_L2_pos": 13},
            {"idx_L2_slat": 12, "idx_L2_pos": 12},
        ],
    
        2: [
            {"idx_L2_slat": 2, "idx_L2_pos": 13},
            {"idx_L2_slat": 3, "idx_L2_pos": 13},
            {"idx_L2_slat": 3, "idx_L2_pos": 12},
        ],
    
        4: [
            {"idx_L2_slat": 4,  "idx_L2_pos": 13},
            {"idx_L2_slat": 13, "idx_L2_pos": 13},
            {"idx_L2_slat": 13, "idx_L2_pos": 12},
        ],
        5: [
            {"idx_L2_slat": 5, "idx_L2_pos": 13},
            {"idx_L2_slat": 6, "idx_L2_pos": 13},
            {"idx_L2_slat": 6, "idx_L2_pos": 12},
        ],

        7: [
            {"idx_L2_slat": 7,   "idx_L2_pos": 13},
            {"idx_L2_slat": 14,  "idx_L2_pos": 13},
            {"idx_L2_slat": 14,  "idx_L2_pos": 12},  
        ],
        
        8: [
            {"idx_L2_slat": 8,   "idx_L2_pos": 13},
            {"idx_L2_slat": 11,  "idx_L2_pos": 13},
            {"idx_L2_slat": 11,  "idx_L2_pos": 12},  
        ],
        
        10: [
            {"idx_L2_slat": 10,  "idx_L2_pos": 13},
            {"idx_L2_slat": 15,  "idx_L2_pos": 13},
            {"idx_L2_slat": 15,  "idx_L2_pos": 12},  
        ],
    }


    def link_slat_count_L2_L1(
        megastructure,
        linked_handles,
        L1_slats_range,     # List of 16 L1 slats, e.g. [65..80]
        L2_slats_ordered,   # List of 16 L2 slats to enumerate, e.g. [56,54,...,33]
        base_L1,            # 1 or 17
        L2_starts_with_1_16=True, # True if slats c and b are 1 to 16, False if 17 to 32
        force_base_L2=None, # For seed, when no alternance of 1 to 16 and 17 to 32
        skip_offsets=None, # If needed to skip L1 offsetts (to skip L2 slats corresponding to these L1 offsets)
    ):
        slats = megastructure.slats
        get_key = get_slat_key
        
        # Skip offsets
        if skip_offsets is None:
            skip_offsets = set()
        else:
            skip_offsets = set(skip_offsets)
    
        # Which rule table to use for each L1 index in the block
        idxL1_to_table = {
            0: slat_count_c,
            1: slat_count_h,
            2: slat_count_f,
            3: slat_count_g,
            4: slat_count_a,
            6: slat_count_b,
            9: slat_count_e,
            12: slat_count_d,
        }
    
        for idx_L1, rule_table in idxL1_to_table.items():
    
            # 1) Which L1 slat
            L1_slat = L1_slats_range[idx_L1]
    
            # 2) For this slat, loop over all L1 position offsets defined in the table
            #    (0,1,2,4,5,7,8,10, depending on which table)
            for pos_offset, triple_specs in rule_table.items():
                
                if pos_offset in skip_offsets:
                    continue
    
                # L1 position = base_L1 + offset
                pos_L1 = base_L1 + pos_offset
    
                # Build L1 handle
                L1_coord = slats[get_key(1, L1_slat)].slat_position_to_coordinate[pos_L1]
                L1_handle = (1, 'top', L1_coord)
    
                linked_handles.setdefault(L1_handle, [])
    
                # 3) For each of the 3 L2 links
                for spec in triple_specs:
                    idx_L2 = spec["idx_L2_slat"]      # index in L2_slats_ordered
                    pos_L2_offset = spec["idx_L2_pos"]
    
                    slat_L2 = L2_slats_ordered[idx_L2]
    
                    # base_L2 depends on idx_L2
                    special = [0,2,3,8,9,10,11,15]
                    
                    if force_base_L2 is not None:
                        base_L2 = force_base_L2

                    else:
                        if L2_starts_with_1_16:
                            base_L2 = 1 if idx_L2 in special else 17
                        else:
                            base_L2 = 17 if idx_L2 in special else 1
    
                    pos_L2 = base_L2 + pos_L2_offset
    
                    L2_coord = slats[get_key(2, slat_L2)].slat_position_to_coordinate[pos_L2]
                    L2_handle = (2, 'bottom', L2_coord)
    
                    if L2_handle not in linked_handles[L1_handle]:
                        linked_handles[L1_handle].append(L2_handle)
    
    
    blocks_for_slat_count = [
        # (L1_start, L2_slats_ordered, base_L1, L2_starts_with_1_16, force_base_L2, skip_offsets)
        #First row from the bottom, from left to right
        (  1,                                                list(range( 1,17)), 17, False,    17, None),
        ( 17,                                                list(range(17,33)), 17, False,    17, None),
        #Second row from the bottom, from left to right
        ( 65, [ 56, 54, 53, 52, 50, 48, 46, 44, 43, 42, 41, 40, 38, 36, 34, 33], 17,  True,  None, None),
        (  1, [ 56, 55, 53, 52, 51, 49, 47, 45, 43, 42, 41, 40, 39, 37, 35, 33],  1, False,  None, None),
        ( 17, [ 79, 78, 76, 74, 73, 72, 71, 70, 68, 66, 64, 62, 61, 60, 59, 57],  1, False,  None, None),
        ( 81, [ 80, 78, 77, 75, 73, 72, 71, 70, 69, 67, 65, 63, 61, 60, 59, 58], 17,  True,  None, None),
        #Third row from the bottom, from left to right
        ( 97, [137,134,133,132,130,128,126,124,123,122,121,120,118,116,114,113], 17,  True,  None, None),
        ( 65, [137,135,133,132,131,129,127,125,123,122,121,120,119,117,115,113],  1, False,  None, None),
        ( 49, [ 96,135, 94, 93,131,129,127,125, 88, 87, 86, 85,119,117,115, 81], 17,  True,  None, [1,4,5,6,7,12,13,14]),
        ( 33, [ 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81],  1, False,  None, None),
        (129, [160, 95,157,155, 92, 91, 90, 89,149,147,145,143, 84, 83, 82,138], 17,  True,  None, [0,2,3,8,9,10,11,15]),
        ( 81, [160,159,157,155,154,153,152,151,149,147,145,143,142,141,140,138],  1, False,  None, None),
        (113, [161,159,158,156,154,153,152,151,150,148,146,144,142,141,140,139], 17,  True,  None, None),
        #Fourth row from the bottom, from left to right
        ( 97, [186,185,183,182,181,179,177,175,173,172,171,169,168,166,164,162],  1, False,  None, None),
        (193, [112,185,110,109,181,179,177,175,104,103,102,101,168,166,164, 97], 17,  True,  None, [1,4,5,6,7,12,13,14]),
        ( 49, [112,111,110,109,108,107,106,105,104,103,102,101,100, 99, 98, 97],  1, False,  None, None),
        (145, [217,111,219,220,108,107,106,105,225,226,227,228,100, 99, 98,232], 17,  True,  None, [0,2,3,8,9,10,11,15]),
        (129,                                              list(range(217,233)),  1, False,  None, None),
        (113, [215,214,212,210,209,208,207,206,204,201,199,197,196,195,194,192],  1, False,  None, None),
        #Fifth row from the bottom, from left to right
        (257, [281,478,279,278,479,480,481,482,273,272,271,269,483,484,485,265], 17,  True,  None, [0,2,3,8,9,10,11,15]),
        (193, [281,280,279,278,277,276,275,274,273,272,271,269,268,267,266,265],  1, False,  None, None),
        (145, [248,247,246,245,244,243,242,241,240,239,238,237,236,235,234,233],  1, False,  None, None),
        (177, [264,263,262,261,260,259,258,257,256,255,254,253,252,251,250,249],  1, False,  None, None),
        (289, [486,263,487,488,260,259,258,257,489,490,491,492,252,251,250,493], 17,  True,  None, [1,4,5,6,7,12,13,14]),
        #Sixth row from the bottom, from left to right
        (257, [346,345,344,343,342,340,339,338,337,336,335,334,333,332,331,330],  1, False,  None, None),
        (209, [429,428,427,426,425,424,423,422,421,420,419,418,417,416,415,414],  1, False,  None, None),
        (161, [445,444,443,442,441,440,439,438,437,436,435,434,433,432,431,430],  1, False,  None, None),
        (289, [388,386,385,384,383,382,381,380,379,378,377,376,375,374,373,372],  1, False,  None, None),
        #Seventh row from the bottom, from left to right
        (321,                                              list(range(446,462)),  1, False,  None, None),
        (417, [509,508,507,506,505,504,503,502,501,500,499,498,497,496,495,494],  1, False,  None, None),
        (337,                                              list(range(462,478)),  1, False,  None, None),   
        
    ]
    
    # L2 to L1 (Tiles)
    def link_tile_L2_L1(
        megastructure,
        linked_handles,
        L1_tile_slats,      # List of 16 L1 slats
        L2_tile_slats,      # List of 16 L2 slats to enumerate
        base_tile_L1,       # 1 or 17
        pattern_L2=True,    # True = first pattern, False = swapped
        skip_offsets=None   # If needed to skip L1 offsetts (to skip L2 slats corresponding to these L1 offsets)
    ):
    
        slats = megastructure.slats
        get_key = get_slat_key
    
        if skip_offsets is None:
            skip_offsets = set()
        else:
            skip_offsets = set(skip_offsets)
    
        # Base pattern for L2
        pattern_true  = [1,17,1,1,17,17,17,17,1,1,1,1,17,17,17,1]
        pattern_false = [17 if x == 1 else 1 for x in pattern_true]
    
        base_map = pattern_true if pattern_L2 else pattern_false
    
        # Loop over L1 offsets
        for offset_tile_L1 in range(16):
    
            if offset_tile_L1 in skip_offsets:
                continue
    
            pos_L1 = base_tile_L1 + offset_tile_L1
            index_L2_slat = offset_tile_L1
    
            base_L2 = base_map[index_L2_slat]
            L2_slat = L2_tile_slats[index_L2_slat]
    
            # Loop over index L1 slats
            for index_L1_slat, L1_slat in enumerate(L1_tile_slats):
    
                coord_L1 = slats[get_key(1, L1_slat)].slat_position_to_coordinate[pos_L1]
                L1_handle = (1, 'top', coord_L1)
    
                offset_tile_L2 = index_L1_slat
                pos_L2 = base_L2 + offset_tile_L2
    
                coord_L2 = slats[get_key(2, L2_slat)].slat_position_to_coordinate[pos_L2]
                L2_handle = (2, 'bottom', coord_L2)
    
                # Append safely to dictionary
                existing = linked_handles.get(L1_handle)
    
                if existing is None:
                    linked_handles[L1_handle] = [L2_handle]
                elif isinstance(existing, list):
                    if L2_handle not in existing:
                        existing.append(L2_handle)
                else:
                    if existing != L2_handle:
                        linked_handles[L1_handle] = [existing, L2_handle]
                        
    tiles = [
        # (L1_start, L2_slats_list, base_tile_L1, pattern_L2, skip_offsets)
        # Tile L
        ( 65, [186,184,183,182,180,178,176,174,173,172,171,169,167,165,163,162], 17, True, None),
        # Tile R
        ( 81, [216,214,213,211,209,208,207,206,205,203,200,198,196,195,194,193], 17, True, None),
        # Tiles A
        ( 49, [281,478,279,278,479,480,481,482,273,272,271,269,483,484,485,265], 17, True, [1,4,5,6,7,12,13,14]),
        ( 49, [429,345,427,426,342,340,339,338,421,420,419,418,333,332,331,414], 17, True, [1,4,5,6,7,12,13,14]),
        ( 49, [509,447,507,506,450,451,452,453,501,500,499,498,458,459,460,494], 17, True, [1,4,5,6,7,12,13,14]),
        ( 49, [248,280,246,245,277,276,275,274,240,239,238,237,268,267,266,233], 17, True, [1,4,5,6,7,12,13,14]),
        ( 49, [445,428,443,442,425,424,423,422,437,436,435,434,417,416,415,430], 17, True, [1,4,5,6,7,12,13,14]),
        ( 49, [264,247,262,261,244,243,242,241,256,255,254,253,236,235,234,249], 17, True, [1,4,5,6,7,12,13,14]),
        # Tiles B
        (257, [112,185,110,109,181,179,177,175,104,103,102,101,168,166,164, 97], 17, True, [0,2,3,8,9,10,11,15]),
        (257, [ 96,135, 94, 93,131,129,127,125, 88, 87, 86, 85,119,117,115, 81], 17, True, [0,2,3,8,9,10,11,15]),
        (257, [ 79, 55, 76, 74, 51, 49, 47, 45, 68, 66, 64, 62, 39, 37, 35, 57], 17, True, [0,2,3,8,9,10,11,15]),
        # Tiles C
        (289, [215,218,212,210,221,222,223,224,204,201,199,197,229,230,231,192], 17, True, [1,4,5,6,7,12,13,14]),
        (289, [160, 95,157,155, 92, 91, 90, 89,149,147,145,143, 84, 83, 82,138], 17, True, [1,4,5,6,7,12,13,14]),
        (289, [ 79, 55, 76, 74, 51, 49, 47, 45, 68, 66, 64, 62, 39, 37, 35, 57], 17, True, [1,4,5,6,7,12,13,14]),
        # Tiles D
        (193, [217,111,219,220,108,107,106,105,225,226,227,228,100, 99, 98,232], 17, True, [1,4,5,6,7,12,13,14]),
        (193, [346,345,344,343,342,340,339,338,337,336,335,334,333,332,331,330], 17, True, [1,4,5,6,7,12,13,14]),
        (193, [388,444,385,384,441,440,439,438,379,378,377,376,433,432,431,372], 17, True, [1,4,5,6,7,12,13,14]),
        (193,                                              list(range(446,462)), 17, True, [1,4,5,6,7,12,13,14]),
        (193, [462,508,464,465,505,504,503,502,470,471,472,473,497,496,495,477], 17, True, [1,4,5,6,7,12,13,14]),
        # Tiles E
        (129, [248,280,246,245,277,276,275,274,240,239,238,237,268,267,266,233], 17, True, [0,2,3,8,9,10,11,15]),
        (129, [264,247,262,261,244,243,242,241,256,255,254,253,236,235,234,249], 17, True, [0,2,3,8,9,10,11,15]),
        (129, [486,263,487,488,260,259,258,257,489,490,491,492,252,251,250,493], 17, True, [0,2,3,8,9,10,11,15]),
        (129, [445,428,443,442,425,424,423,422,437,436,435,434,417,416,415,430], 17, True, [0,2,3,8,9,10,11,15]),
        (129, [388,444,385,384,441,440,439,438,379,378,377,376,433,432,431,372], 17, True, [0,2,3,8,9,10,11,15]),
        (129, [462,508,464,465,505,504,503,502,470,471,472,473,497,496,495,477], 17, True, [0,2,3,8,9,10,11,15]),
        # Tiles F
        (145, [215,218,212,210,221,222,223,224,204,201,199,197,229,230,231,192], 17, True, [0,2,3,8,9,10,11,15]),
        (145, [429,345,427,426,342,340,339,338,421,420,419,418,333,332,331,414], 17, True, [0,2,3,8,9,10,11,15]),
        (145, [509,447,507,506,450,451,452,453,501,500,499,498,458,459,460,494], 17, True, [0,2,3,8,9,10,11,15]),
        (145,                                              list(range(462,478)), 17, True, [0,2,3,8,9,10,11,15]),
        (145, [388,386,385,384,383,382,381,380,379,378,377,376,375,374,373,372], 17, True, [0,2,3,8,9,10,11,15]),
        # Tile X
        ( 65, [281,478,279,278,479,480,481,482,273,272,271,269,483,484,485,265],  1, False, [0,2,3,8,9,10,11,15]),
        # Tile Y
        ( 81, [486,263,487,488,260,259,258,257,489,490,491,492,252,251,250,493],  1, False, [1,4,5,6,7,12,13,14]),
    ]


    #------ Build everything

    linked_handles = {}
    
    # SLAT COUNTS
    
    #L3-L2
    for l3_list, pair_list in L3_to_L2_blocks:
        merge_no_overwrite(
            linked_handles,
            build_l3_block_pairs(megastructure, l3_list, pair_list),
        )
    
    #L2 to L1 (slat count = 8)
    for L1_start, L2_slats, base_L1, L2_flag, force_L2, offsets_skipped in blocks_for_slat_count:
        link_slat_count_L2_L1(
            megastructure,
            linked_handles,
            list(range(L1_start, L1_start + 16)),
            L2_slats,
            base_L1,
            L2_flag,
            force_L2,
            offsets_skipped,
        )
    
    #L2 to L1 (tiles)
    for L1_start, L2_slats, base_tile_L1, pattern_L2, offset_skips in tiles:
    
        link_tile_L2_L1(
            megastructure,
            linked_handles,
            list(range(L1_start, L1_start + 16)),
            L2_slats,
            base_tile_L1,
            pattern_L2,
            offset_skips
        )

# ---- Evolution

    evolve_manager = EvolveManager(megastructure,
                                   unique_handle_sequences=64,
                                   early_max_valency_stop=1, evolution_population=50,
                                   generational_survivors=3,
                                   mutation_rate=1,
                                   process_count=5,
                                   random_seed=12,
                                   remove_duplicates_in_layers=[(3, 'antihandles')],
                                   evolution_generations=30000,
                                   split_sequence_handles=False,
                                   progress_bar_update_iterations=10,
                                   repeating_unit_constraints={'link_handles': linked_handles},
                                   log_tracking_directory='/Users/juliefinkel/Documents/Projects_postdoc/CrissCross/Sierpinski_triangle_designs/Gadgets_design/Count_8/Output_handles_gadgets')
    
    evolve_manager.run_full_experiment(logging_interval=10)