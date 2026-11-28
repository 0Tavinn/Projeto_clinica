__kernel void contains_bytes(
    __global const uchar *haystack,
    __global const ulong *offsets,
    const ulong count,
    __global const uchar *needle,
    const ulong needle_len,
    __global uchar *matches
) {
    const ulong i = get_global_id(0);
    if (i >= count) return;
    const ulong start = offsets[i];
    const ulong end = offsets[i + 1];
    uchar found = 0;
    if (needle_len > 0 && end >= start && end - start >= needle_len) {
        for (ulong p = start; p + needle_len <= end; ++p) {
            ulong j = 0;
            while (j < needle_len && haystack[p + j] == needle[j]) ++j;
            if (j == needle_len) { found = 1; break; }
        }
    }
    matches[i] = found;
}
