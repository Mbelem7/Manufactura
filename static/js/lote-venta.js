document.addEventListener("DOMContentLoaded", () => {
    // Selector de lote de las lineas de venta. Cada fila (elemento con data-lote-fila)
    // tiene un select de producto y uno de lote; las opciones de lote vienen del
    // servidor en orden FIFO (la primera de cada producto es la mas antigua).

    function opcionesDelProducto(fila) {
        const producto = fila.querySelector("select[name='producto_id']").value;

        return Array.from(
            fila.querySelectorAll("select[name='lote_id'] option[data-producto]")
        ).filter((option) => option.dataset.producto === producto);
    }


    function mostrarAviso(fila) {
        const select = fila.querySelector("select[name='lote_id']");
        const aviso = fila.querySelector("[data-aviso-fifo]");
        const cantidad = fila.querySelector("input[name='cantidad']");
        const elegida = select.selectedOptions[0];
        const masAntigua = opcionesDelProducto(fila)[0];

        // La cantidad no puede pasar de lo disponible en el lote
        if (cantidad) {
            if (elegida && elegida.dataset.existencia) {
                cantidad.max = elegida.dataset.existencia;
            } else {
                cantidad.removeAttribute("max");
            }
        }

        if (!aviso) {
            return;
        }

        if (elegida && masAntigua && elegida !== masAntigua) {
            aviso.textContent =
                "El lote " + masAntigua.dataset.codigo +
                " es más antiguo. Por FIFO conviene despachar ese primero.";
            aviso.hidden = false;
        } else {
            aviso.hidden = true;
        }
    }


    function filtrarLotes(fila) {
        const select = fila.querySelector("select[name='lote_id']");
        const vacio = select.querySelector("option[value='']");
        const visibles = opcionesDelProducto(fila);

        select.querySelectorAll("option[data-producto]").forEach((option) => {
            const visible = visibles.includes(option);
            option.hidden = !visible;
            option.disabled = !visible;
        });

        // Se preselecciona el lote mas antiguo (FIFO)
        select.value = visibles.length ? visibles[0].value : "";

        if (vacio) {
            vacio.textContent = fila.querySelector("select[name='producto_id']").value
                ? (visibles.length ? "Seleccione un lote" : "Sin lotes disponibles")
                : "Elija primero un producto";
        }

        mostrarAviso(fila);
    }


    document.addEventListener("change", (event) => {
        const fila = event.target.closest("[data-lote-fila]");

        if (!fila) {
            return;
        }

        if (event.target.matches("select[name='producto_id']")) {
            filtrarLotes(fila);
        } else if (event.target.matches("select[name='lote_id']")) {
            mostrarAviso(fila);
        }
    });
});
