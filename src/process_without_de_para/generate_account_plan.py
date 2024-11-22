import io


class GenerateAccountPlanWithoutDePara(object):
    def __init__(self, dataFile: io.TextIOWrapper):
        self.__dataFile = dataFile
        pass

    def __verificar_tipo_conta(self) -> int:
        """
        :return -> 1 plano de contas como codigo ; 2 plano de contas como classificacao
        """

        self.__dataFile.seek(0)
        while line := self.__dataFile.readline():
            try:
                if line.startswith('|I050|'):
                    campos = line.strip().split('|')
                    tipo = campos[4].strip()
                    conta = campos[6].strip()

                    if tipo == 'A':  # Verifica se é uma conta analítica
                        # Verificação das condições para classificação
                        if "." in conta:
                            return 2  # Considera como classificação
                        elif len(conta) >= 7 and (conta[-1] == '0' or conta[-2] == '0' or conta[-3] == '0'):
                            return 2  # Considera como classificação
                        else:
                            return 1  # Considera como código
            except Exception as e:
                pass
                # print(e)
        return 2

    def __processar_ecd_classificacao(self):
        contas = []

        self.__dataFile.seek(0)
        while line := self.__dataFile.readline():
            try:
                if line.startswith('|I050|'):
                    # Extração dos campos relevantes
                    campos = line.strip().split('|')
                    classificacao_str = campos[6].strip()  # O valor do campo Classificação
                    descricao = campos[8].strip()
                    tipo = campos[4].strip()
                    data = campos[2].strip()

                    # Adiciona a linha processada à lista de contas
                    contas.append([None, classificacao_str, descricao, tipo, data])  # Código será atribuído após ordenação
                if line.startswith('|I150|'):
                    break
            except Exception as e:
                pass
                # print(e)

        # Ordena a lista de contas pela classificação antes de criar o código sequencial
        contas.sort(key=lambda x: x[1])

        # Construção do código sequencial após a ordenação
        sequencial = 1
        for conta in contas:
            conta[0] = f"{sequencial:06d}"  # Formata o código como um número sequencial de 6 dígitos
            sequencial += 1

        return contas

    def __processar_ecd_codigo(self):
        contas = []
        classificacao = {}  # Dicionário para armazenar a classificação por nível
        nivel_6_existe = False
        contagem_nivel = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}  # Contadores para cada nível

        self.__dataFile.seek(0)
        while line := self.__dataFile.readline():
            try:
                if line.startswith('|I050|'):
                    campos = line.strip().split('|')
                    nivel = int(campos[5].strip())
                    if nivel == 6:
                        nivel_6_existe = True
                        break
                if line.startswith('|I150|'):
                    break
            except Exception as e:
                pass
                # print(e)

        self.__dataFile.seek(0)
        while line := self.__dataFile.readline():
            try:
                if line.startswith('|I050|'):
                    # Extração dos campos relevantes
                    campos = line.strip().split('|')
                    codigo = campos[6].strip()
                    descricao = campos[8].strip()
                    tipo = campos[4].strip()
                    nivel = int(campos[5].strip())
                    data = campos[2].strip()

                    # Atualiza a contagem do nível atual
                    contagem_nivel[nivel] += 1
                    # Reseta as contagens dos níveis inferiores
                    for i in range(nivel + 1, 7):
                        contagem_nivel[i] = 0

                    # Construção da classificação
                    if nivel == 1:
                        classificacao[nivel] = f"{contagem_nivel[nivel]}"
                    else:
                        parent_level = nivel - 1
                        if nivel == 5:
                            if nivel_6_existe:
                                # Se nível 6 existir, o nível 5 deve ter formato X.X.XX.XX.XX
                                classificacao[nivel] = f"{classificacao[parent_level]}.{contagem_nivel[nivel]:02}"
                            else:
                                # Se nível 6 não existir, o nível 5 deve ter formato X.X.XX.XX.XXXXX
                                classificacao[nivel] = f"{classificacao[parent_level]}.{contagem_nivel[nivel]:05}"
                        elif nivel == 6:
                            classificacao[nivel] = f"{classificacao[parent_level]}.{contagem_nivel[nivel]:05}"
                        else:
                            # Níveis 2, 3, e 4 sempre com dois dígitos
                            classificacao[nivel] = f"{classificacao[parent_level]}.{contagem_nivel[nivel]:02}"
                    # Adiciona a linha processada à lista de contas
                    contas.append([codigo, classificacao[nivel], descricao, tipo, data])
                if line.startswith('|I150|'):
                    break
            except Exception as e:
                pass
                # print(e)

        return contas

    def __associar_conta_referencial(self, contas, is_classificacao=False):
        conta_referencial_map = {}

        codigoConta = ''
        tipoConta = ''

        self.__dataFile.seek(0)
        while line := self.__dataFile.readline():
            try:
                if line.startswith('|I050|'):
                    campos = line.strip().split('|')
                    codigoConta = campos[6].strip()
                    tipoConta = campos[4].strip()

                if line.startswith('|I051|') and tipoConta == 'A':
                    campos = line.strip().split('|')
                    conta_referencial = campos[3].strip()
                    conta_referencial_map[codigoConta] = conta_referencial

                if line.startswith('|I150|'):
                    break

            except Exception as e:
                pass

        for conta in contas:
            chave = conta[1] if is_classificacao else conta[0]

            if chave in conta_referencial_map:
                conta.append(conta_referencial_map[chave])
            else:
                conta.append(None)

        return contas

    def process(self):
        tipo_conta = self.__verificar_tipo_conta()

        contas = []
        if tipo_conta == 1:
            contas = self.__processar_ecd_codigo()
            contas = self.__associar_conta_referencial(contas, is_classificacao=False)
        elif tipo_conta == 2:
            contas = self.__processar_ecd_classificacao()
            contas = self.__associar_conta_referencial(contas, is_classificacao=True)

        return [contas, tipo_conta]
