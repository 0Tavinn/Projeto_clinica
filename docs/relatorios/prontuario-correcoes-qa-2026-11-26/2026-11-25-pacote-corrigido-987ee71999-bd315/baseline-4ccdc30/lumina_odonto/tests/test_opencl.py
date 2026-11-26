from app.opencl_search import normalize, sequential_search, OpenCLSearch, OpenCLUnavailable

def test_cpu_search():
    assert sequential_search(['Evolução Clínica', 'Consulta inicial', 'EVOLUCAO'], 'evolucao') == [0, 2]

def test_opencl_matches_cpu_when_available():
    data = ['Clínica odontológica', 'Consulta de retorno', 'CLINICA']
    try:
        opencl = OpenCLSearch()
    except OpenCLUnavailable:
        return
    assert opencl.search(data, 'clinica') == sequential_search(data, 'clinica')
