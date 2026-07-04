// Lógica del buscador encadenado Provincia -> Cantón -> Distrito -> Barrio.
// No usa librerías externas; todo se apoya en DATA_CR (definido en data.js).

(function () {
  function normalizar(texto) {
    return texto
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function formatearNumero(numero, pad) {
    return pad ? String(numero).padStart(2, "0") : String(numero);
  }

  function etiqueta(item, pad) {
    return `${formatearNumero(item.numero, pad)} - ${item.nombre || "(sin nombre)"}`;
  }

  const MAX_SUGERENCIAS = 50;

  class Nivel {
    constructor({ input, lista, obtenerOpciones, onSeleccionar, onLimpiar, pad = false }) {
      this.input = input;
      this.lista = lista;
      this.obtenerOpciones = obtenerOpciones;
      this.onSeleccionar = onSeleccionar;
      this.onLimpiar = onLimpiar || function () {};
      this.pad = pad;
      this.seleccion = null;

      this.input.addEventListener("input", () => {
        if (this.seleccion && this.input.value !== etiqueta(this.seleccion)) {
          this.seleccion = null;
          this.onLimpiar();
        }
        this.mostrarSugerencias();
      });
      this.input.addEventListener("focus", () => this.mostrarSugerencias());
      this.input.addEventListener("blur", () => {
        setTimeout(() => this.ocultarSugerencias(), 150);
      });
    }

    habilitar(placeholder) {
      this.input.disabled = false;
      this.input.placeholder = placeholder;
    }

    deshabilitar(placeholder) {
      this.input.disabled = true;
      this.input.value = "";
      this.input.placeholder = placeholder;
      this.seleccion = null;
      this.ocultarSugerencias();
    }

    limpiarSeleccion() {
      this.seleccion = null;
      this.input.value = "";
    }

    mostrarSugerencias() {
      if (this.input.disabled) return;

      const opciones = this.obtenerOpciones();
      const consulta = normalizar(this.input.value);
      const coincidencias = opciones
        .filter((o) => normalizar(o.nombre).includes(consulta))
        .slice(0, MAX_SUGERENCIAS);

      this.lista.innerHTML = "";
      if (coincidencias.length === 0) {
        this.lista.hidden = true;
        return;
      }

      for (const opcion of coincidencias) {
        const li = document.createElement("li");
        li.textContent = etiqueta(opcion, this.pad);
        li.tabIndex = 0;
        li.addEventListener("mousedown", (evento) => {
          evento.preventDefault(); // evita que el input pierda foco antes del click
          this.seleccionar(opcion);
        });
        this.lista.appendChild(li);
      }
      this.lista.hidden = false;
    }

    seleccionar(opcion) {
      this.seleccion = opcion;
      this.input.value = etiqueta(opcion, this.pad);
      this.ocultarSugerencias();
      this.onSeleccionar(opcion);
    }

    ocultarSugerencias() {
      this.lista.hidden = true;
    }
  }

  const nivelProvincia = new Nivel({
    input: document.getElementById("input-provincia"),
    lista: document.getElementById("sugerencias-provincia"),
    obtenerOpciones: () => DATA_CR.provincias,
    onSeleccionar: () => {
      resetearDesde("canton");
      nivelCanton.habilitar("Escribe el nombre del cantón...");
      actualizarResultado();
    },
    onLimpiar: () => resetearDesde("canton"),
  });

  const nivelCanton = new Nivel({
    input: document.getElementById("input-canton"),
    lista: document.getElementById("sugerencias-canton"),
    obtenerOpciones: () => (nivelProvincia.seleccion ? nivelProvincia.seleccion.cantones : []),
    onSeleccionar: () => {
      resetearDesde("distrito");
      nivelDistrito.habilitar("Escribe el nombre del distrito...");
      actualizarResultado();
    },
    onLimpiar: () => resetearDesde("distrito"),
    pad: true,
  });

  const nivelDistrito = new Nivel({
    input: document.getElementById("input-distrito"),
    lista: document.getElementById("sugerencias-distrito"),
    obtenerOpciones: () => (nivelCanton.seleccion ? nivelCanton.seleccion.distritos : []),
    onSeleccionar: () => {
      resetearDesde("barrio");
      nivelBarrio.habilitar("Escribe el nombre del barrio...");
      actualizarResultado();
    },
    onLimpiar: () => resetearDesde("barrio"),
    pad: true,
  });

  const nivelBarrio = new Nivel({
    input: document.getElementById("input-barrio"),
    lista: document.getElementById("sugerencias-barrio"),
    obtenerOpciones: () => (nivelDistrito.seleccion ? nivelDistrito.seleccion.barrios : []),
    onSeleccionar: () => actualizarResultado(),
    onLimpiar: () => actualizarResultado(),
    pad: true,
  });

  function resetearDesde(nivel) {
    if (nivel === "canton") {
      nivelCanton.deshabilitar("Elige primero la provincia");
      nivelDistrito.deshabilitar("Elige primero el cantón");
      nivelBarrio.deshabilitar("Elige primero el distrito");
    } else if (nivel === "distrito") {
      nivelDistrito.deshabilitar("Elige primero el cantón");
      nivelBarrio.deshabilitar("Elige primero el distrito");
    } else if (nivel === "barrio") {
      nivelBarrio.deshabilitar("Elige primero el distrito");
    }
    actualizarResultado();
  }

  function setTexto(idFila, seleccion, pad) {
    document.querySelector(`#${idFila} span`).textContent = seleccion ? etiqueta(seleccion, pad) : "—";
  }

  function actualizarResultado() {
    setTexto("resultado-provincia", nivelProvincia.seleccion, nivelProvincia.pad);
    setTexto("resultado-canton", nivelCanton.seleccion, nivelCanton.pad);
    setTexto("resultado-distrito", nivelDistrito.seleccion, nivelDistrito.pad);
    setTexto("resultado-barrio", nivelBarrio.seleccion, nivelBarrio.pad);

    const niveles = [nivelProvincia, nivelCanton, nivelDistrito, nivelBarrio];
    const codigoEl = document.getElementById("codigo-completo");
    const btnCopiar = document.getElementById("btn-copiar");

    if (niveles.every((n) => n.seleccion)) {
      const codigo = niveles.map((n) => formatearNumero(n.seleccion.numero, n.pad)).join("-");
      codigoEl.textContent = codigo;
      btnCopiar.disabled = false;
      btnCopiar.dataset.codigo = codigo;
    } else {
      codigoEl.textContent = "—";
      btnCopiar.disabled = true;
      delete btnCopiar.dataset.codigo;
    }
  }

  document.getElementById("btn-reiniciar").addEventListener("click", () => {
    nivelProvincia.limpiarSeleccion();
    resetearDesde("canton");
  });

  document.getElementById("btn-copiar").addEventListener("click", async () => {
    const btn = document.getElementById("btn-copiar");
    const codigo = btn.dataset.codigo;
    if (!codigo) return;

    try {
      await navigator.clipboard.writeText(codigo);
    } catch (error) {
      const area = document.createElement("textarea");
      area.value = codigo;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      document.body.removeChild(area);
    }

    const mensaje = document.getElementById("mensaje-copiado");
    mensaje.hidden = false;
    setTimeout(() => {
      mensaje.hidden = true;
    }, 1500);
  });

  const CLAVE_TEMA = "tema";
  const btnTema = document.getElementById("btn-tema");

  function temaActual() {
    const explicito = document.documentElement.dataset.tema;
    if (explicito === "claro" || explicito === "oscuro") return explicito;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro";
  }

  function aplicarTema(tema) {
    document.documentElement.dataset.tema = tema;
    btnTema.textContent = tema === "oscuro" ? "☀️" : "🌙";
    btnTema.setAttribute("aria-label", tema === "oscuro" ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
  }

  aplicarTema(temaActual());

  btnTema.addEventListener("click", () => {
    const nuevoTema = temaActual() === "oscuro" ? "claro" : "oscuro";
    localStorage.setItem(CLAVE_TEMA, nuevoTema);
    aplicarTema(nuevoTema);
  });

  actualizarResultado();
})();
