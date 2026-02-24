"""
bayesian/diagnostico_poluicao.py — Rede Bayesiana para Diagnóstico de Poluição

Implementa uma rede bayesiana simples para inferir a probabilidade de
poluição grave no estuário do Rio Poxim, com base em evidências ambientais.

Estrutura da Rede (DAG):

    Maré ──────────┐
                   ├──→ SaúdeMangue ──┐
    ProximidadeUrb ┘                  ├──→ PoluiçãoGrave
    ProximidadeUrb ───────────────────┘

Nós:
    - Maré: {baixa, alta} — nível de maré observado
    - ProximidadeUrbana: {sim, não} — se a posição está próxima a zona urbana
    - SaúdeMangue: {boa, degradada} — estado observado do manguezal
    - PoluiçãoGrave: {sim, não} — variável de interesse (query)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

# ============================================================================
# Protocolo do ChemicalSensor (para type checking sem importação circular)
# ============================================================================

@runtime_checkable
class ChemicalSensor(Protocol):
    """Protocolo compatível com interfaces.sensor_interfaces.ChemicalSensor."""

    def get_contamination_reading(self) -> dict[str, float]:
        ...


CPT_MARE: dict[str, float] = {
    "baixa": 0.55,
    "alta": 0.45,
}

CPT_PROXIMIDADE_URBANA: dict[str, float] = {
    "sim": 0.35,
    "não": 0.65,
}

CPT_SAUDE_MANGUE: dict[tuple[str, str], dict[str, float]] = {
    ("baixa", "sim"):  {"boa": 0.15, "degradada": 0.85},
    ("baixa", "não"):  {"boa": 0.55, "degradada": 0.45},
    ("alta", "sim"):   {"boa": 0.30, "degradada": 0.70},
    ("alta", "não"):   {"boa": 0.80, "degradada": 0.20},
}

CPT_POLUICAO_GRAVE: dict[tuple[str, str], dict[str, float]] = {
    ("degradada", "sim"):  {"sim": 0.90, "não": 0.10},
    ("degradada", "não"):  {"sim": 0.45, "não": 0.55},
    ("boa", "sim"):        {"sim": 0.25, "não": 0.75},
    ("boa", "não"):        {"sim": 0.05, "não": 0.95},
}

class RedeBayesianaPoluicao:
    """
    Rede Bayesiana para diagnóstico de poluição no estuário.
    Implementa inferência por enumeração exata (AIMA, Fig. 13.9)
    para calcular P(PoluiçãoGrave | evidências).
    """

    def __init__(self) -> None:
        self.cpt_mare = CPT_MARE
        self.cpt_proximidade = CPT_PROXIMIDADE_URBANA
        self.cpt_saude = CPT_SAUDE_MANGUE
        self.cpt_poluicao = CPT_POLUICAO_GRAVE

    def inferir(self, evidencias: dict[str, str]) -> float:
        """
        Calcula P(PoluiçãoGrave=sim | evidências) por enumeração exata.
        """
        mares = [evidencias["mare"]] if "mare" in evidencias else ["baixa", "alta"]
        proximidades = (
            [evidencias["proximidade_urbana"]]
            if "proximidade_urbana" in evidencias
            else ["sim", "não"]
        )
        saudes = (
            [evidencias["saude_mangue"]]
            if "saude_mangue" in evidencias
            else ["boa", "degradada"]
        )

        prob_poluicao = 0.0
        prob_total = 0.0

        for mare in mares:
            p_mare = self.cpt_mare[mare]

            for prox in proximidades:
                p_prox = self.cpt_proximidade[prox]

                for saude in saudes:
                    p_saude = self.cpt_saude[(mare, prox)][saude]

                    p_pol_sim = self.cpt_poluicao[(saude, prox)]["sim"]
                    p_pol_nao = self.cpt_poluicao[(saude, prox)]["não"]

                    p_conjunta_sim = p_mare * p_prox * p_saude * p_pol_sim
                    p_conjunta_nao = p_mare * p_prox * p_saude * p_pol_nao

                    prob_poluicao += p_conjunta_sim
                    prob_total += p_conjunta_sim + p_conjunta_nao

        if prob_total == 0:
            return 0.0
        return prob_poluicao / prob_total

    def inferir_completa(
        self, evidencias: dict[str, str]
    ) -> dict[str, float]:
        """Retorna distribuição completa P(PoluiçãoGrave | evidências)."""
        p_sim = self.inferir(evidencias)
        return {"sim": round(p_sim, 4), "não": round(1 - p_sim, 4)}

    def classificar_risco(self, probabilidade: float) -> str:
        """Classifica o nível de risco com base na probabilidade."""
        if probabilidade < 0.25:
            return "🟢 BAIXO"
        elif probabilidade < 0.50:
            return "🟡 MODERADO"
        elif probabilidade < 0.75:
            return "🟠 ALTO"
        else:
            return "🔴 CRÍTICO"

    def converter_leitura_sensor(
        self,
        leitura: dict[str, float],
        posicao_urbana: bool = False,
    ) -> dict[str, str]:
        """
        Converte leitura do ChemicalSensor em evidências bayesianas.
        """
        evidencias: dict[str, str] = {}

        od = leitura.get("OD", 6.5)
        if od < 4.0:
            evidencias["saude_mangue"] = "degradada"
        elif od >= 6.0:
            evidencias["saude_mangue"] = "boa"

        mercurio = leitura.get("mercurio", 0.0)
        chumbo = leitura.get("chumbo", 0.0)

        if mercurio > 0.001 or chumbo > 0.01 or posicao_urbana:
            evidencias["proximidade_urbana"] = "sim"
        else:
            evidencias["proximidade_urbana"] = "não"

        return evidencias

    def diagnosticar_com_sensor(
        self,
        sensor: ChemicalSensor,
        mare: str = "baixa",
        posicao_urbana: bool = False,
    ) -> dict:
        """
        Diagnóstico completo usando leitura do ChemicalSensor.
        Integra o sensor de contaminantes com a rede bayesiana para
        produzir um diagnóstico de poluição acionável.
        """
        leitura = sensor.get_contamination_reading()

        evidencias = self.converter_leitura_sensor(leitura, posicao_urbana)
        evidencias["mare"] = mare

        prob = self.inferir(evidencias)
        classificacao = self.classificar_risco(prob)

        return {
            "probabilidade_poluicao_grave": round(prob, 4),
            "classificacao_risco": classificacao,
            "evidencias_usadas": evidencias,
            "leitura_sensor": leitura,
            "distribuicao": self.inferir_completa(evidencias),
        }


def main() -> None:
    """Demonstração da rede bayesiana com diferentes cenários."""

    print("=" * 70)
    print("  🧬 REDE BAYESIANA — Diagnóstico de Poluição")
    print("  📍 Estuário do Rio Poxim, Aracaju-SE")
    print("  📖 Referência: AIMA — Capítulos 12 e 13")
    print("=" * 70)

    rede = RedeBayesianaPoluicao()

    cenarios = [
        {
            "nome": "Cenário 1: Maré baixa + Zona urbana (pior caso)",
            "evidencias": {"mare": "baixa", "proximidade_urbana": "sim"},
        },
        {
            "nome": "Cenário 2: Maré alta + Zona natural (melhor caso)",
            "evidencias": {"mare": "alta", "proximidade_urbana": "não"},
        },
        {
            "nome": "Cenário 3: Maré baixa + Mangue degradado",
            "evidencias": {"mare": "baixa", "saude_mangue": "degradada"},
        },
        {
            "nome": "Cenário 4: Zona urbana + Mangue degradado (sem info de maré)",
            "evidencias": {"proximidade_urbana": "sim", "saude_mangue": "degradada"},
        },
        {
            "nome": "Cenário 5: Apenas maré alta (info mínima)",
            "evidencias": {"mare": "alta"},
        },
        {
            "nome": "Cenário 6: Sem evidências (prior)",
            "evidencias": {},
        },
    ]

    for cenario in cenarios:
        print(f"\n{'─' * 70}")
        print(f"  🔬 {cenario['nome']}")
        print(f"  Evidências: {cenario['evidencias']}")

        dist = rede.inferir_completa(cenario["evidencias"])
        prob = dist["sim"]
        risco = rede.classificar_risco(prob)

        print(f"  P(PoluiçãoGrave = sim) = {prob:.4f}")
        print(f"  P(PoluiçãoGrave = não) = {dist['não']:.4f}")
        print(f"  Classificação: {risco}")

    print(f"\n\n{'═' * 70}")
    print("  🧪 INTEGRAÇÃO COM ChemicalSensor")
    print(f"{'═' * 70}")

    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    from interfaces.sensor_interfaces import SimulatedChemical

    sensor_limpo = SimulatedChemical(default_readings={
        "mercurio": 0.0001,
        "chumbo": 0.005,
        "OD": 7.0
    })

    resultado = rede.diagnosticar_com_sensor(
        sensor=sensor_limpo,
        mare="alta",
        posicao_urbana=False,
    )

    print(f"\n  📊 Sensor: Água limpa (OD=7.0, metais baixos)")
    print(f"  Leitura: {resultado['leitura_sensor']}")
    print(f"  Evidências: {resultado['evidencias_usadas']}")
    print(f"  P(Poluição Grave) = {resultado['probabilidade_poluicao_grave']:.4f}")
    print(f"  Risco: {resultado['classificacao_risco']}")

    sensor_poluido = SimulatedChemical(default_readings={
        "mercurio": 0.05,
        "chumbo": 0.12,
        "OD": 2.8
    })

    resultado = rede.diagnosticar_com_sensor(
        sensor=sensor_poluido,
        mare="baixa",
        posicao_urbana=True,
    )

    print(f"\n  📊 Sensor: Água contaminada (OD=2.8, metais altos)")
    print(f"  Leitura: {resultado['leitura_sensor']}")
    print(f"  Evidências: {resultado['evidencias_usadas']}")
    print(f"  P(Poluição Grave) = {resultado['probabilidade_poluicao_grave']:.4f}")
    print(f"  Risco: {resultado['classificacao_risco']}")

    sensor_moderado = SimulatedChemical(default_readings={
        "mercurio": 0.01,
        "chumbo": 0.02,
        "OD": 4.5
    })

    resultado = rede.diagnosticar_com_sensor(
        sensor=sensor_moderado,
        mare="baixa",
        posicao_urbana=False,
    )

    print(f"\n  📊 Sensor: Valores moderados (OD=4.5, metais médios)")
    print(f"  Leitura: {resultado['leitura_sensor']}")
    print(f"  Evidências: {resultado['evidencias_usadas']}")
    print(f"  P(Poluição Grave) = {resultado['probabilidade_poluicao_grave']:.4f}")
    print(f"  Risco: {resultado['classificacao_risco']}")

    print(f"\n{'═' * 70}")
    print("  ✅ Demonstração concluída")
    print(f"{'═' * 70}\n")


if __name__ == "__main__":
    main()
