"""Invariantes de los workflows que publican releases rolling.

Por que existe este test (audit ago-2026): el release `hires-loop-rolling` tenia
DOS escritores —el cron `hires_visible_cache` (*/10) y el `hires_loop_backfill`
manual— y solo uno declaraba grupo de concurrency. Como la accion compartida
publica un SNAPSHOT COMPLETO del release, lanzar el backfill mientras corria el
cron borraba la ventana rodante de 8 h ya acumulada, que despues tardaba otras
~8 h en reconstruirse frame a frame.

El invariante que se hace cumplir aca es el que impide que eso vuelva:
todo tag de release rolling tiene que tener UN solo grupo de concurrency
compartido por todos sus escritores.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOWS = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows"
ACTION = "./.github/actions/gh-release-snapshot"


def _load_workflows() -> dict[str, dict]:
    return {
        p.name: yaml.safe_load(p.read_text(encoding="utf-8"))
        for p in sorted(WORKFLOWS.glob("*.yml"))
    }


def _release_writers() -> dict[str, set[tuple[str, str | None]]]:
    """tag -> {(workflow, grupo de concurrency)} para cada publicacion al release.

    Los tags dinamicos (`${{ ... }}`, caso `backfill_build`) quedan fuera: el tag
    depende de inputs del run, asi que dos runs solo colisionan si el usuario pide
    a mano la misma fecha y el mismo volcan. No es la clase de carrera que este
    test vigila.
    """
    writers: dict[str, set[tuple[str, str | None]]] = {}
    for name, wf in _load_workflows().items():
        grupo = (wf.get("concurrency") or {}).get("group")
        for job in (wf.get("jobs") or {}).values():
            for step in job.get("steps") or []:
                if step.get("uses") != ACTION:
                    continue
                tag = (step.get("with") or {}).get("tag", "")
                if "${{" in tag:
                    continue
                writers.setdefault(tag, set()).add((name, grupo))
    return writers


def test_hay_escritores_de_releases_rolling():
    """Guard del guard: si la accion se renombra, el test no puede pasar vacio."""
    writers = _release_writers()
    assert "hires-loop-rolling" in writers, (
        f"No se encontro ningun publicador de hires-loop-rolling. "
        f"Tags detectados: {sorted(writers)}"
    )


@pytest.mark.parametrize("tag", sorted(_release_writers()))
def test_un_solo_grupo_de_concurrency_por_tag(tag):
    escritores = _release_writers()[tag]
    grupos = {grupo for _, grupo in escritores}

    faltantes = sorted(wf for wf, grupo in escritores if grupo is None)
    assert not faltantes, (
        f"El tag '{tag}' se publica desde {faltantes} sin `concurrency.group`. "
        "Sin grupo, dos runs pueden pisarse el snapshot completo del release."
    )

    assert len(grupos) == 1, (
        f"El tag '{tag}' tiene escritores en grupos distintos: "
        f"{sorted(escritores)}. Todos deben compartir el mismo grupo para "
        "serializarse; si no, un run borra lo que el otro acababa de publicar."
    )


def test_backfill_de_loops_comparte_grupo_con_el_cron():
    """Caso concreto del audit, escrito aparte para que el diff se lea solo."""
    escritores = _release_writers()["hires-loop-rolling"]
    por_wf = dict(escritores)
    assert por_wf.get("hires_visible_cache.yml") == "hires-cache"
    assert por_wf.get("hires_loop_backfill.yml") == "hires-cache"


def test_la_accion_sube_antes_de_borrar():
    """El release no debe quedar nunca vacio a mitad de una publicacion.

    Con `borrar todo -> subir en batches con sleep` pasaban minutos con el
    release vacio o a medio poblar, en CADA corrida del cron de 10 min y sin
    necesidad de ninguna carrera. El orden correcto es subir con --clobber y
    recien despues podar los huerfanos.
    """
    action = yaml.safe_load(
        (WORKFLOWS.parent / "actions" / "gh-release-snapshot" / "action.yml")
        .read_text(encoding="utf-8")
    )
    scripts = "\n".join(s.get("run", "") for s in action["runs"]["steps"])

    i_upload = scripts.find("gh release upload")
    i_delete = scripts.find("gh release delete-asset")
    assert i_upload != -1 and i_delete != -1, "Faltan los comandos de gh en la accion"
    assert i_upload < i_delete, (
        "La accion borra assets antes de subir: el release queda vacio durante "
        "la publicacion. Subir con --clobber primero, podar huerfanos despues."
    )
    assert "--clobber" in scripts, "El upload debe usar --clobber para reemplazar en sitio"
