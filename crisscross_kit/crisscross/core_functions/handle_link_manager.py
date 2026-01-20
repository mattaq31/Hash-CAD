from collections import defaultdict

import numpy as np


class HandleLinkManager:
    """
    Manages handle linking information for megastructures.

    This class tracks three types of constraints on handle values:

    1. **Linked Groups**: Handles that must share the same value. When one handle
       in a group changes, all others must change to match.
       - Stored in: handle_link_to_group (key → group_id) and
         handle_group_to_link (group_id → list of keys)

    2. **Enforced Values**: Groups that must have a specific handle value.
       - Stored in: handle_group_to_value (group_id → value)

    3. **Blocked Handles**: Individual handles that must be zero (deleted).
       - Stored in: handle_blocks (list of keys)

    Handle keys use the convention: (slat_name, position, helix_side)
    Example: ('layer1-slat5', 3, 2) means position 3 on H2 side of layer1-slat5.

    All group IDs are numeric integers, persisted to file on export.
    """
    def __init__(self, handle_link_df=None):
        # read handle linking information from sheet (if available)
        self.handle_link_to_group = {}
        self.handle_group_to_link = defaultdict(list)
        self.handle_group_to_value = defaultdict(int)
        self.handle_blocks = []
        self.max_group_id = 0  # tracks highest numeric group ID

        if handle_link_df is not None:
            # Two-pass algorithm to avoid group ID collisions

            # PASS 1: Find max group ID across all data
            for i in range(0, len(handle_link_df), 6):
                for index_jump in [3, 5]:  # group columns are at offset 3 (h5) and 5 (h2)
                    for group in handle_link_df.iloc[i + index_jump][1:]:
                        try:
                            if not np.isnan(group):
                                self.max_group_id = max(self.max_group_id, int(group))
                        except (TypeError, ValueError):
                            pass  # Skip non-numeric values

            # PASS 2: Process data and assign new IDs to enforced-only values
            for i in range(0, len(handle_link_df), 6):
                slat_name = handle_link_df.iloc[i, 0]
                for side, index_jump in zip([5, 2], [2, 4]):
                    for index, (enforce_val, group) in enumerate(zip(handle_link_df.iloc[i + index_jump][1:], handle_link_df.iloc[i + index_jump + 1][1:])):

                        key = (slat_name, index + 1, side)  # for slat links, convention is (slat_name, position, helix_side)

                        # Check for NaN values
                        enforce_is_nan = False
                        group_is_nan = False
                        try:
                            enforce_is_nan = np.isnan(enforce_val)
                        except (TypeError, ValueError):
                            pass
                        try:
                            group_is_nan = np.isnan(group)
                        except (TypeError, ValueError):
                            pass

                        if enforce_is_nan and group_is_nan:
                            continue  # full skip

                        if enforce_val == 0:  # just add to block list and move on
                            self.handle_blocks.append(key)

                        elif not enforce_is_nan and group_is_nan:  # no special group, just enforce a specific value at this position
                            # Assign new numeric ID (avoids collision via two-pass algorithm)
                            self.max_group_id += 1
                            new_group = self.max_group_id
                            self.handle_group_to_value[new_group] = int(enforce_val)
                            self.handle_group_to_link[new_group].append(key)
                            self.handle_link_to_group[key] = new_group

                        elif not group_is_nan:  # set a specific group link
                            group_int = int(group)
                            self.handle_link_to_group[key] = group_int
                            self.handle_group_to_link[group_int].append(key)
                            if not enforce_is_nan:
                                if group_int in self.handle_group_to_value and self.handle_group_to_value[group_int] != int(enforce_val):
                                    raise RuntimeError('Cannot enforce multiple values to the same slat handle group.'
                                                       '  Check the slat_handle_links sheet.')
                                self.handle_group_to_value[group_int] = int(enforce_val)

    def get_enforce_value(self, access_key):
        if access_key in self.handle_blocks:
            return 0
        if access_key in self.handle_link_to_group:
            group = self.handle_link_to_group[access_key]
            if group in self.handle_group_to_value:
                return self.handle_group_to_value[group]
        return None

    def add_block(self, key):
        """
        Adds a block to a handle.
        :param key: (slat_name, position, side)
        """
        if key not in self.handle_blocks:
            self.handle_blocks.append(key)

    def remove_block(self, key):
        """
        Removes a block from a handle.
        :param key: (slat_name, position, side)
        """
        if key in self.handle_blocks:
            self.handle_blocks.remove(key)

    def remove_link(self, key):
        """
        Removes a link from a handle.
        :param key: (slat_name, position, side)
        """
        group = self.handle_link_to_group.get(key, None)
        if group is not None:
            self.handle_group_to_link[group].remove(key)
            del self.handle_link_to_group[key]
            if len(self.handle_group_to_link[group]) == 0:
                del self.handle_group_to_link[group]
                if group in self.handle_group_to_value:
                    del self.handle_group_to_value[group]

    def remove_group(self, group_id):
        """
        Removes an entire handle link group.
        :param group_id: Group ID to remove
        """
        if group_id in self.handle_group_to_link:
            for key in self.handle_group_to_link[group_id]:
                del self.handle_link_to_group[key]
            del self.handle_group_to_link[group_id]
            if group_id in self.handle_group_to_value:
                del self.handle_group_to_value[group_id]

    def _merge_groups(self, target_group, source_group):
        """
        Merge source_group into target_group, moving all keys and enforced values.

        :param target_group: Group ID to merge into (this group survives)
        :param source_group: Group ID to be dissolved (this group is deleted)
        :raises RuntimeError: If groups have conflicting enforced values
        """
        for key in self.handle_group_to_link[source_group]:
            self.handle_link_to_group[key] = target_group
            self.handle_group_to_link[target_group].append(key)
        del self.handle_group_to_link[source_group]

        if source_group in self.handle_group_to_value:
            if target_group in self.handle_group_to_value and self.handle_group_to_value[target_group] != self.handle_group_to_value[source_group]:
                raise RuntimeError('Cannot merge two handle link groups with different enforced values.')
            self.handle_group_to_value[target_group] = self.handle_group_to_value[source_group]
            del self.handle_group_to_value[source_group]

    def add_link(self, key_1, key_2):
        """
        Adds a link between two handles.
        :param key_1: (slat_name, position, side)
        :param key_2: (slat_name, position, side)
        """

        group_1 = self.handle_link_to_group.get(key_1, None)
        group_2 = self.handle_link_to_group.get(key_2, None)

        if group_1 is None and group_2 is None:
            # create new group using numeric ID (saved to file)
            new_group = self.max_group_id + 1
            self.max_group_id += 1
            self.handle_link_to_group[key_1] = new_group
            self.handle_link_to_group[key_2] = new_group
            self.handle_group_to_link[new_group].extend([key_1, key_2])

        elif group_1 is not None and group_2 is None:
            # add key_2 to group_1
            self.handle_link_to_group[key_2] = group_1
            self.handle_group_to_link[group_1].append(key_2)
        elif group_1 is None and group_2 is not None:
            # add key_1 to group_2
            self.handle_link_to_group[key_1] = group_2
            self.handle_group_to_link[group_2].append(key_1)

        elif group_1 != group_2:
            # merge group_2 into group_1
            self._merge_groups(group_1, group_2)

    def clear_all(self):
        self.handle_link_to_group = {}
        self.handle_group_to_link = defaultdict(list)
        self.handle_group_to_value = defaultdict(int)
        self.handle_blocks = []
        self.max_group_id = 0
