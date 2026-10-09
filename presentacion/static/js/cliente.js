/**
 * Lógica de la vista de Cliente (capa de Presentación).
 *
 * Responsabilidades permitidas aquí: capturar datos de formularios,
 * validaciones SINTÁCTICAS (campos vacíos, formato), armar la
 * solicitud HTTP y pintar la respuesta del servidor.
 *
 * Prohibido aquí (y de hecho no implementado): calcular descuentos,
 * calcular DevPoints, decidir ascensos de nivel, o decidir si un
 * pedido puede registrarse. Todo eso lo decide el backend; esta
 * vista solo muestra el resultado que llega en la respuesta JSON.
 *
 * Nota sobre sessionStorage: se usa ÚNICAMENTE para recordar qué
 * cliente quedó identificado en esta pestaña del navegador (un simple
 * puntero de sesión). Ningún dato de negocio (productos, pedidos,
 * saldos) se lee de almacenamiento local: todo se recarga desde el
 * servidor en cada operación.
 */

const estado = {
  cliente: null,
  productos: [],
  carrito: [], // { producto_id, nombre, precio_base, cantidad, stock_disponible }
};

document.addEventListener("DOMContentLoaded", () => {
  cargarProductos();
  configurarEventos();
  intentarRestaurarSesion();
});

function configurarEventos() {
  document.getElementById("form-identificar").addEventListener("submit", onIdentificar);
  document.getElementById("form-registrar").addEventListener("submit", onRegistrar);
  document.getElementById("btn-cerrar-sesion").addEventListener("click", cerrarSesion);
  document.getElementById("tipo-pedido").addEventListener("change", onCambiarTipoPedido);
  document.getElementById("form-pedido").addEventListener("submit", onCrearPedido);
  document.getElementById("btn-actualizar-pedidos").addEventListener("click", cargarMisPedidos);
}

function intentarRestaurarSesion() {
  const idGuardado = sessionStorage.getItem("cafe_overflow_cliente_id");
  if (!idGuardado) return;
  Api.obtenerCliente(idGuardado)
    .then(setClienteActivo)
    .catch(() => sessionStorage.removeItem("cafe_overflow_cliente_id"));
}

/* ---------------- Identificación / registro ---------------- */

async function onIdentificar(evento) {
  evento.preventDefault();
  const correo = document.getElementById("input-correo-identificar").value.trim();
  if (!correo) return;
  try {
    const cliente = await Api.obtenerClientePorCorreo(correo);
    setClienteActivo(cliente);
    mostrarMensaje(`Bienvenido de nuevo, ${cliente.nombre}.`, "exito");
  } catch (e) {
    if (e.status === 404) {
      document.getElementById("input-correo-registrar").value = correo;
      document.getElementById("form-registrar").classList.remove("oculto");
      mostrarMensaje("No encontramos ese correo. Crea tu cuenta DevCoffee.", "info");
    } else {
      mostrarMensaje(e.message, "error");
    }
  }
}

async function onRegistrar(evento) {
  evento.preventDefault();
  const nombre = document.getElementById("input-nombre-registrar").value.trim();
  const correo = document.getElementById("input-correo-registrar").value.trim();
  try {
    const cliente = await Api.crearCliente({ nombre, correo });
    document.getElementById("form-registrar").classList.add("oculto");
    setClienteActivo(cliente);
    mostrarMensaje(`Cuenta creada. ¡Bienvenido, ${cliente.nombre}!`, "exito");
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

function setClienteActivo(cliente) {
  estado.cliente = cliente;
  sessionStorage.setItem("cafe_overflow_cliente_id", cliente.id);
  document.getElementById("panel-identificacion").classList.add("oculto");
  document.getElementById("panel-cliente").classList.remove("oculto");
  document.getElementById("txt-nombre-cliente").textContent = cliente.nombre;
  document.getElementById("txt-correo-cliente").textContent = cliente.correo;
  const badgeNivel = document.getElementById("badge-nivel");
  badgeNivel.textContent = etiquetaNivel(cliente.nivel_lealtad);
  badgeNivel.className = `badge ${cliente.nivel_lealtad}`;
  document.getElementById("txt-devpoints").textContent = cliente.saldo_devpoints;
  document.getElementById("txt-acumulado").textContent = formatoCOP(cliente.monto_acumulado_compras);
  document.getElementById("input-puntos").max = cliente.saldo_devpoints;
  document.getElementById("seccion-pedido").classList.remove("oculto");
  document.getElementById("seccion-mis-pedidos").classList.remove("oculto");
  verificarPedidoPendiente();
  cargarMisPedidos();
}

function cerrarSesion() {
  estado.cliente = null;
  estado.carrito = [];
  sessionStorage.removeItem("cafe_overflow_cliente_id");
  document.getElementById("panel-identificacion").classList.remove("oculto");
  document.getElementById("panel-cliente").classList.add("oculto");
  document.getElementById("seccion-pedido").classList.add("oculto");
  document.getElementById("seccion-mis-pedidos").classList.add("oculto");
  renderCarrito();
}

/* ---------------- Menú / productos ---------------- */

async function cargarProductos() {
  try {
    estado.productos = await Api.listarProductos();
    renderProductos();
  } catch (e) {
    mostrarMensaje("No se pudo cargar el menú: " + e.message, "error");
  }
}

function renderProductos() {
  const rejilla = document.getElementById("rejilla-productos");
  rejilla.innerHTML = "";
  estado.productos.forEach((p) => {
    const tarjeta = document.createElement("div");
    tarjeta.className = "tarjeta-producto";
    const sinStock = p.stock_disponible <= 0;
    tarjeta.innerHTML = `
      <div class="icono">☕</div>
      <h3>${escaparHtml(p.nombre)}</h3>
      <div class="precio">${formatoCOP(p.precio_base)}</div>
      <div class="stock ${p.stock_disponible <= 5 ? "bajo" : ""}">
        ${sinStock ? "Agotado" : `Stock: ${p.stock_disponible}`}
      </div>
      <div class="fila-cantidad">
        <input type="number" min="1" max="${p.stock_disponible}" value="1" ${sinStock ? "disabled" : ""} />
        <button ${sinStock ? "disabled" : ""}>Agregar</button>
      </div>
    `;
    const input = tarjeta.querySelector("input");
    const boton = tarjeta.querySelector("button");
    boton.addEventListener("click", () => {
      const cantidad = parseInt(input.value, 10);
      if (!cantidad || cantidad <= 0) {
        mostrarMensaje("Ingresa una cantidad válida.", "error");
        return;
      }
      agregarAlCarrito(p, cantidad);
    });
    rejilla.appendChild(tarjeta);
  });
}

/* ---------------- Carrito ---------------- */

function agregarAlCarrito(producto, cantidad) {
  const existente = estado.carrito.find((l) => l.producto_id === producto.id);
  if (existente) {
    existente.cantidad += cantidad;
  } else {
    estado.carrito.push({
      producto_id: producto.id,
      nombre: producto.nombre,
      precio_base: producto.precio_base,
      cantidad,
    });
  }
  renderCarrito();
  mostrarMensaje(`${producto.nombre} agregado al carrito.`, "exito");
}

function quitarDelCarrito(productoId) {
  estado.carrito = estado.carrito.filter((l) => l.producto_id !== productoId);
  renderCarrito();
}

function renderCarrito() {
  const lista = document.getElementById("carrito-lista");
  const vacio = document.getElementById("carrito-vacio");
  lista.innerHTML = "";
  if (estado.carrito.length === 0) {
    vacio.classList.remove("oculto");
  } else {
    vacio.classList.add("oculto");
  }
  let subtotalEstimado = 0;
  estado.carrito.forEach((linea) => {
    subtotalEstimado += linea.precio_base * linea.cantidad;
    const div = document.createElement("div");
    div.className = "carrito-item";
    div.innerHTML = `
      <span>${escaparHtml(linea.nombre)} × ${linea.cantidad}</span>
      <span>${formatoCOP(linea.precio_base * linea.cantidad)}
        <button type="button" class="pequeno peligro">✕</button>
      </span>
    `;
    div.querySelector("button").addEventListener("click", () => quitarDelCarrito(linea.producto_id));
    lista.appendChild(div);
  });
  document.getElementById("txt-subtotal-estimado").textContent = formatoCOP(subtotalEstimado);
  document.getElementById("resultado-pedido").classList.add("oculto");
}

function onCambiarTipoPedido() {
  const tipo = document.getElementById("tipo-pedido").value;
  document.getElementById("campo-mesa").classList.toggle("oculto", tipo !== "MESA");
}

/* ---------------- Pedido pendiente / creación ---------------- */

async function verificarPedidoPendiente() {
  if (!estado.cliente) return;
  try {
    const { tiene_pedido_pendiente } = await Api.tienePedidoPendiente(estado.cliente.id);
    const aviso = document.getElementById("aviso-pedido-pendiente");
    const boton = document.querySelector("#form-pedido button[type=submit]");
    aviso.classList.toggle("oculto", !tiene_pedido_pendiente);
    boton.disabled = tiene_pedido_pendiente;
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

async function onCrearPedido(evento) {
  evento.preventDefault();
  if (!estado.cliente) {
    mostrarMensaje("Identifícate primero.", "error");
    return;
  }
  if (estado.carrito.length === 0) {
    mostrarMensaje("Tu carrito está vacío.", "error");
    return;
  }
  const tipoPedido = document.getElementById("tipo-pedido").value;
  const numeroMesaRaw = document.getElementById("input-mesa").value;
  const puntosRaw = document.getElementById("input-puntos").value;

  const payload = {
    cliente_id: estado.cliente.id,
    tipo_pedido: tipoPedido,
    numero_mesa: tipoPedido === "MESA" ? parseInt(numeroMesaRaw, 10) || null : null,
    puntos_a_redimir: parseInt(puntosRaw, 10) || 0,
    items: estado.carrito.map((l) => ({ producto_id: l.producto_id, cantidad: l.cantidad })),
  };

  try {
    const pedido = await Api.crearPedido(payload);
    mostrarMensaje(`Pedido #${pedido.id} creado correctamente.`, "exito");
    mostrarResultadoPedido(pedido);
    estado.carrito = [];
    renderCarrito();
    document.getElementById("input-puntos").value = 0;
    // El servidor ya descontó stock y DevPoints redimidos: refrescamos todo.
    await cargarProductos();
    const clienteActualizado = await Api.obtenerCliente(estado.cliente.id);
    setClienteActivo(clienteActualizado);
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

function mostrarResultadoPedido(pedido) {
  const caja = document.getElementById("resultado-pedido");
  caja.classList.remove("oculto");
  caja.innerHTML = `
    <div class="linea"><span>Subtotal</span><span>${formatoCOP(pedido.subtotal)}</span></div>
    <div class="linea"><span>Descuento por nivel</span><span>- ${formatoCOP(pedido.descuento_nivel)}</span></div>
    <div class="linea"><span>Descuento DevPoints</span><span>- ${formatoCOP(pedido.descuento_devpoints)}</span></div>
    <div class="linea total"><span>Total a pagar</span><span>${formatoCOP(pedido.total_calculado)}</span></div>
    <p class="texto-apagado">Estado: <span class="badge ${pedido.estado}">${etiquetaEstado(pedido.estado)}</span></p>
  `;
}

/* ---------------- Mis pedidos ---------------- */

async function cargarMisPedidos() {
  if (!estado.cliente) return;
  try {
    const pedidos = await Api.listarPedidosDeCliente(estado.cliente.id);
    const contenedor = document.getElementById("lista-mis-pedidos");
    contenedor.innerHTML = "";
    if (pedidos.length === 0) {
      contenedor.innerHTML = '<p class="texto-apagado">Aún no tienes pedidos.</p>';
      return;
    }
    pedidos.forEach((pedido) => {
      const div = document.createElement("div");
      div.className = "panel";
      div.style.marginBottom = "0.8rem";
      const itemsTexto = pedido.items
        .map((i) => `${i.cantidad} × producto #${i.producto_id}`)
        .join(", ");
      div.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong>Pedido #${pedido.id}</strong>
          <span class="badge ${pedido.estado}">${etiquetaEstado(pedido.estado)}</span>
        </div>
        <p class="texto-apagado">${pedido.tipo_pedido === "MESA" ? "Mesa " + pedido.numero_mesa : "Para llevar"} · ${pedido.fecha}</p>
        <p class="texto-apagado">${itemsTexto}</p>
        <p><strong>Total: ${formatoCOP(pedido.total_calculado)}</strong></p>
      `;
      contenedor.appendChild(div);
    });
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

function escaparHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}
