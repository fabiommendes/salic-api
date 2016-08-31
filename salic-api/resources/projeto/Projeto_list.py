import sys
sys.path.append('../../')
from ..ResourceBase import *
from models import ProjetoModelObject
from ..serialization import listify_queryset
from ..format_utils import truncate, remove_blanks, remove_html_tags, HTMLEntitiesToUnicode
from ..sanitization import sanitize


class ProjetoList(ResourceBase):

     def __init__(self):
        super (ProjetoList,self).__init__()

     @app.cache.cached(timeout=app.config['GLOBAL_CACHE_TIMEOUT'], key_prefix=make_key)
     def get(self):

        headers = {}

        if request.args.get('limit') is not None:
            limit = int(request.args.get('limit'))

            if limit > app.config['LIMIT_PAGING']:
                results = {'message' : 'Max limit paging exceeded',
                        'message_code' : 7
                    }
                return self.render(results, status_code = 405)

        else:
            limit = app.config['LIMIT_PAGING']

        if request.args.get('offset') is not None:
            offset = int(request.args.get('offset'))
        else:
            offset = app.config['OFFSET_PAGING']

        PRONAC = None
        nome = None
        proponente = None
        cgccpf = None
        area = None
        segmento = None
        UF = None
        municipio = None
        data_inicio = None
        data_inicio_min = None
        data_inicio_max = None
        data_termino = None
        data_termino_min = None
        data_termino_max = None
        ano_projeto = None

        if request.args.get('limit') is not None:
            limit = int(request.args.get('limit'))

        if request.args.get('offset') is not None:
            offset = int(request.args.get('offset'))

        if request.args.get('PRONAC') is not None:
            PRONAC = request.args.get('PRONAC')

        if request.args.get('nome') is not None:
            nome = request.args.get('nome')

        if request.args.get('proponente') is not None:
            proponente = request.args.get('proponente')

        if request.args.get('cgccpf') is not None:
            cgccpf = request.args.get('cgccpf')

        if request.args.get('area') is not None:
            area = request.args.get('area')

        if request.args.get('segmento') is not None:
            segmento = request.args.get('segmento')

        if request.args.get('segmento') is not None:
            segmento = request.args.get('segmento')

        if request.args.get('UF') is not None:
            UF = request.args.get('UF')

        if request.args.get('municipio') is not None:
            municipio = request.args.get('municipio')

        if request.args.get('data_inicio') is not None:
            data_inicio = request.args.get('data_inicio')

        if request.args.get('data_inicio_min') is not None:
            data_inicio_min = request.args.get('data_inicio_min')

        if request.args.get('data_inicio_max') is not None:
            data_inicio_max = request.args.get('data_inicio_max')

        if request.args.get('data_termino') is not None:
            data_termino = request.args.get('data_termino')

        if request.args.get('data_termino_min') is not None:
            data_termino_min = request.args.get('data_termino_min')

        if request.args.get('data_termino_max') is not None:
            data_termino_max = request.args.get('data_termino_max')

        if request.args.get('ano_projeto') is not None:
            ano_projeto = request.args.get('ano_projeto')

        try:
            Log.debug('Starting database call')
            results, n_records = ProjetoModelObject().all(limit, offset, PRONAC, nome,
                              proponente, cgccpf, area, segmento,
                              UF, municipio, data_inicio, data_inicio_min, data_inicio_max,
                              data_termino, data_termino_min, data_termino_max, ano_projeto)

            Log.debug('Database call was successful')

        except Exception as e:
            Log.error( str(e))
            result = {'message' : 'internal error',
                      'message_code' :  13,
                      'more' : 'something is broken'
                      }
            return self.render(result, status_code = 503)

        if n_records == 0:
            results = {'message' : 'No project was found with your criteria',
                        'message_code' : 11
                        }
            return self.render(results, status_code = 404)

        else :
            headers = {'X-Total-Count' : n_records}

        data = listify_queryset(results)

        for projeto in data:

            "Removing IdPRONAC"
            del projeto['IdPRONAC']

            "Getting rid of blanks"
            projeto["cgccpf"]  = remove_blanks(str(projeto["cgccpf"]))

            "Sanitizing text values"
            projeto['acessibilidade'] = sanitize(projeto['acessibilidade'])
            projeto['objetivos'] = sanitize(projeto['objetivos'])
            projeto['justificativa'] = sanitize(projeto['justificativa'])
            projeto['etapa'] = sanitize(projeto['etapa'])
            projeto['ficha_tecnica'] = sanitize(projeto['ficha_tecnica'])
            projeto['impacto_ambiental'] = sanitize(projeto['impacto_ambiental'])
            projeto['especificacao_tecnica'] = sanitize(projeto['especificacao_tecnica'])
            projeto['estrategia_execucao'] = sanitize(projeto['estrategia_execucao'])
            projeto['providencia'] = sanitize(projeto['providencia'])
            projeto['democratizacao'] =  sanitize(projeto["democratizacao"])

            projeto['sinopse'] = sanitize(projeto["sinopse"],  truncated = False)
            projeto['resumo'] = sanitize(projeto["resumo"],  truncated = False)

        return self.render(data, headers)
