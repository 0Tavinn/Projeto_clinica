import os
import pytest
os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://lumina:lumina@localhost/lumina')
os.environ.setdefault('JWT_SECRET', 'test-only-not-for-production-00000000')
from app.opencl_search import sequential_search, OpenCLSearch, OpenCLUnavailable

def test_cpu_search():
    assert sequential_search(['Evolução Clínica', 'Consulta inicial', 'EVOLUCAO'], 'evolucao') == [0, 2]

@pytest.mark.parametrize('term', ['', '  ', '\u0301'])
def test_cpu_rejects_empty(term):
    with pytest.raises(ValueError):
        sequential_search(['texto'], term)

def test_opencl_matches_cpu_when_available():
    data = ['Clínica odontológica', 'Consulta de retorno', 'CLINICA']
    try:
        opencl = OpenCLSearch()
    except OpenCLUnavailable:
        pytest.skip('Runtime OpenCL indisponível')
    assert opencl.search(data, 'clinica') == sequential_search(data, 'clinica')
    with pytest.raises(ValueError):
        opencl.search(data, '\u0301')
