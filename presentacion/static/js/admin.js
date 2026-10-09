/**
 * Lógica de la vista Administrativa (capa de Presentación).
 *
 * Igual que en cliente.js: solo captura datos, hace validación
 * sintáctica y pinta lo que el backend responde. Las transiciones de
 * estado de pedido que se habilitan en la interfaz son una ayuda
 * visual; la validación real y definitiva ocurre en OrderService.
 */

const TRANSICIONES_UI = {
  PENDING_PAYMENT: "IN_PREPARATION",
  IN_PREPARATION: "READY",
  READY: "DELIVERED",
  DELIVERED: null,
};

let productoEditandoId = null;

document.addEventListener("DOMContentLoaded", () => {
  configurarTabs();
  configurarFormularios();
  cargarProductos();
  cargarClientes();
  cargarPedidos();
});

function configurarTabs() {
  document.querySelectorAll(".tabs button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tabs button").forEach((b) => b.classList.remove("activo"));
      document.querySelectorAll(".pestana").forEach((p) => p.classList.remove("activa"));
      btn.classList.add("activo");
      document.getElementById(btn.dataset.pestana).classList.add("activa");
    });
  });
}

function configurarFormularios() {
  document.getElementById("form-producto").addEventListener("submit", onGuardarProducto);
  document.getElementById("btn-cancelar-edicion").addEventListener("click", cancelarEdicionProducto);
  document.getElementById("form-cliente-admin").addEventListener("submit", onCrearClienteAdmin);
  document.getElementById("btn-actualizar-pedidos-admin").addEventListener("click", cargarPedidos);
}

/* ======================= PRODUCTOS ======================= */

async function cargarProductos() {
  try {
    const productos = await Api.listarProductos(true);
    renderTablaProductos(productos);
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

function renderTablaProductos(productos) {
  const cuerpo = document.getElementById("cuerpo-tabla-productos");
  cuerpo.innerHTML = "";
  productos.forEach((p) => {
    const fila = document.createElement("tr");
    fila.innerHTML = `
      <td>${p.id}</td>
      <td>${escaparHtml(p.nombre)}</td>
      <td>${formatoCOP(p.precio_base)}</td>
      <td>${p.stock_disponible}</td>
      <td>${p.activo ? "Sí" : "No"}</td>
      <td>
        <button class="pequeno" data-accion="editar">Editar</button>
        <input type="number" class="pequeno" style="width:70px;display:inline-block;margin:0 0.3rem;" placeholder="±stock" />
        <button class="pequeno secundario" data-accion="ajustar">Aplicar</button>
      </td>
    `;
    fila.querySelector('[data-accion="editar"]').addEventListener("click", () => cargarProductoEnFormulario(p));
    const inputDelta = fila.querySelector("input");
    fila.querySelector('[data-accion="ajustar"]').addEventListener("click", async () => {
      const delta = parseInt(inputDelta.value, 10);
      if (!delta) {
        mostrarMensaje("Ingresa un valor de ajuste distinto de cero.", "error");
        return;
      }
      try {
        await Api.ajustarInventario(p.id, delta);
        mostrarMensaje(`Stock de '${p.nombre}' actualizado.`, "exito");
        cargarProductos();
      } catch (e) {
        mostrarMensaje(e.message, "error");
      }
    });
    cuerpo.appendChild(fila);
  });
}

function cargarProductoEnFormulario(producto) {
  productoEditandoId = producto.id;
  document.getElementById("titulo-form-producto").textContent = `Editar producto #${producto.id}`;
  document.getElementById("prod-nombre").value = producto.nombre;
  document.getElementById("prod-precio").value = producto.precio_base;
  document.getElementById("prod-stock").value = producto.stock_disponible;
  document.getElementById("prod-stock").disabled = true; // el stock se gestiona con el ajuste de inventario
  document.getElementById("prod-activo").checked = producto.activo;
  document.getElementById("btn-cancelar-edicion").classList.remove("oculto");
  document.getElementById("btn-guardar-producto").textContent = "Guardar cambios";
}

function cancelarEdicionProducto() {
  productoEditandoId = null;
  document.getElementById("form-producto").reset();
  document.getElementById("prod-stock").disabled = false;
  document.getElementById("titulo-form-producto").textContent = "Nuevo producto";
  document.getElementById("btn-cancelar-edicion").classList.add("oculto");
  document.getElementById("btn-guardar-producto").textContent = "Crear producto";
}

async function onGuardarProducto(evento) {
  evento.preventDefault();
  const nombre = document.getElementById("prod-nombre").value.trim();
  const precio = parseInt(document.getElementById("prod-precio").value, 10);
  const stock = parseInt(document.getElementById("prod-stock").value, 10);
  const activo = document.getElementById("prod-activo").checked;

  try {
    if (productoEditandoId) {
      await Api.actualizarProducto(productoEditandoId, { nombre, precio_base: precio, activo });
      mostrarMensaje("Producto actualizado.", "exito");
    } else {
      await Api.crearProducto({ nombre, precio_base: precio, stock_disponible: stock });
      mostrarMensaje("Producto creado.", "exito");
    }
    cancelarEdicionProducto();
    cargarProductos();
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

/* ======================= CLIENTES ======================= */

async function cargarClientes() {
  try {
    const clientes = await Api.listarClientes();
    renderTablaClientes(clientes);
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

function renderTablaClientes(clientes) {
  const cuerpo = document.getElementById("cuerpo-tabla-clientes");
  cuerpo.innerHTML = "";
  clientes.forEach((c) => {
    const fila = document.createElement("tr");
    fila.innerHTML = `
      <td>${c.id}</td>
      <td>${escaparHtml(c.nombre)}</td>
      <td>${escaparHtml(c.correo)}</td>
      <td><span class="badge ${c.nivel_lealtad}">${etiquetaNivel(c.nivel_lealtad)}</span></td>
      <td>${c.saldo_devpoints}</td>
      <td>${formatoCOP(c.monto_acumulado_compras)}</td>
    `;
    cuerpo.appendChild(fila);
  });
}

async function onCrearClienteAdmin(evento) {
  evento.preventDefault();
  const nombre = document.getElementById("cliente-admin-nombre").value.trim();
  const correo = document.getElementById("cliente-admin-correo").value.trim();
  try {
    await Api.crearCliente({ nombre, correo });
    mostrarMensaje("Cliente registrado.", "exito");
    document.getElementById("form-cliente-admin").reset();
    cargarClientes();
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

/* ======================= PEDIDOS ======================= */

async function cargarPedidos() {
  try {
    const pedidos = await Api.listarTodosPedidos();
    renderTablaPedidos(pedidos);
  } catch (e) {
    mostrarMensaje(e.message, "error");
  }
}

function renderTablaPedidos(pedidos) {
  const cuerpo = document.getElementById("cuerpo-tabla-pedidos");
  cuerpo.innerHTML = "";
  pedidos.forEach((p) => {
    const fila = document.createElement("tr");
    const siguiente = TRANSICIONES_UI[p.estado];
    const itemsTexto = p.items.map((i) => `#${i.producto_id} ×${i.cantidad}`).join(", ");
    fila.innerHTML = `
      <td>${p.id}</td>
      <td>${p.cliente_id}</td>
      <td>${p.tipo_pedido === "MESA" ? "Mesa " + p.numero_mesa : "Para llevar"}</td>
      <td>${escaparHtml(itemsTexto)}</td>
      <td>${formatoCOP(p.total_calculado)}</td>
      <td><span class="badge ${p.estado}">${etiquetaEstado(p.estado)}</span></td>
      <td>${siguiente ? `<button class="pequeno">Avanzar a ${etiquetaEstado(siguiente)}</button>` : "—"}</td>
    `;
    if (siguiente) {
      fila.querySelector("button").addEventListener("click", async () => {
        try {
          await Api.cambiarEstadoPedido(p.id, siguiente);
          mostrarMensaje(`Pedido #${p.id} ahora está ${etiquetaEstado(siguiente)}.`, "exito");
          cargarPedidos();
          if (siguiente === "DELIVERED") cargarClientes();
        } catch (e) {
          mostrarMensaje(e.message, "error");
        }
      });
    }
    cuerpo.appendChild(fila);
  });
}

function escaparHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}
