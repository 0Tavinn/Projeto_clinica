// Cada item compara um intervalo semiaberto com o intervalo solicitado.
// long do OpenCL usa 64 bits; não há conversão de datas em ponto flutuante.
__kernel void check_overlap(
    __global const long2 *intervals,
    const long requested_start,
    const long requested_end,
    __global uchar *overlaps
) {
    const size_t i = get_global_id(0);
    const long2 existing = intervals[i];
    overlaps[i] = (existing.x < requested_end && requested_start < existing.y);
}
