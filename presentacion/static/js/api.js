/**
 * Cliente HTTP mínimo hacia la API del servidor.
 *
 * Esta es la ÚNICA pieza de la capa de Presentación que envía
 * solicitudes HTTP. No decide reglas de negocio: solo transporta
 * datos capturados en los formularios y muestra lo que el backend
 * responde (incluyendo errores de negocio).
 */

const Api = (() => {
  async function solicitar(metodo, ruta, cuerpo) {
    const opciones = {
      method: metodo,
      headers: { "Content-Type": "application/json" },
    };
    if (cuerpo !== undefined) {
      opciones.body = JSON.stringify(cuerpo);
    }
    const respuesta = await fetch(ruta, opciones);
    let datos = null;
    try {
      datos = await respuesta.json();
    } catch (_) {
      datos = null;
    }
    if (!respuesta.ok) {
      const error = new Error((datos && datos.error) || `Error HTTP ${respuesta.status}`);
      error.status = respuesta.status;
      error.tipo = datos && datos.tipo;
      throw error;
    }
    return datos;
  }

  return {
    get: (ruta) => solicitar("GET", ruta),
    post: (ruta, cuerpo) => solicitar("POST", ruta, cuerpo),
    put: (ruta, cuerpo) => solicitar("PUT", ruta, cuerpo),
    patch: (ruta, cuerpo) => solicitar("PATCH", ruta, cuerpo),

    // Productos
    listarProductos: (todos = false) => solicitar("GET", `/api/productos${todos ? "?todos=1" : ""}`),
    crearProducto: (datos) => solicitar("POST", "/api/productos", datos),
    actualizarProducto: (id, datos) => solicitar("PUT", `/api/productos/${id}`, datos),
    ajustarInventario: (id, delta) => solicitar("POST", `/api/productos/${id}/inventario`, { delta }),

    // Clientes
    listarClientes: () => solicitar("GET", "/api/clientes"),
    crearCliente: (datos) => solicitar("POST", "/api/clientes", datos),
    obtenerClientePorCorreo: (correo) => solicitar("GET", `/api/clientes/correo/${encodeURIComponent(correo)}`),
    obtenerCliente: (id) => solicitar("GET", `/api/clientes/${id}`),

    // Pedidos
    listarTodosPedidos: () => solicitar("GET", "/api/pedidos"),
    listarPedidosDeCliente: (clienteId) => solicitar("GET", `/api/clientes/${clienteId}/pedidos`),
    tienePedidoPendiente: (clienteId) => solicitar("GET", `/api/clientes/${clienteId}/pedido-pendiente`),
    crearPedido: (datos) => solicitar("POST", "/api/pedidos", datos),
    cambiarEstadoPedido: (id, estado) => solicitar("PATCH", `/api/pedidos/${id}/estado`, { estado }),
  };
})();

/** Muestra un mensaje tipo toast en #zona-mensajes (éxito / error / info). */
function mostrarMensaje(texto, tipo = "info") {
  let zona = document.getElementById("zona-mensajes");
  if (!zona) {
    zona = document.createElement("div");
    zona.id = "zona-mensajes";
    document.body.appendChild(zona);
  }
  const div = document.createElement("div");
  div.className = `mensaje ${tipo}`;
  div.textContent = texto;
  zona.appendChild(div);
  setTimeout(() => div.remove(), 4500);
}

function formatoCOP(valor) {
  return "$" + Number(valor || 0).toLocaleString("es-CO");
}

function etiquetaEstado(estado) {
  const nombres = {
    PENDING_PAYMENT: "Pendiente de pago",
    IN_PREPARATION: "En preparación",
    READY: "Listo",
    DELIVERED: "Entregado",
  };
  return nombres[estado] || estado;
}

function etiquetaNivel(nivel) {
  const nombres = { JUNIOR: "Junior", MID: "Mid", SENIOR: "Senior" };
  return nombres[nivel] || nivel;
}
