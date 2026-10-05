document.addEventListener("DOMContentLoaded", () => {
    const addButton = document.getElementById("addDispatchItemButton");
    const tableBody = document.getElementById("dispatchItemsTableBody");

    if (!addButton || !tableBody) {
        return;
    }

    const createRow = () => {
        const row = document.createElement("tr");

        row.classList.add("dispatch-item-row");

        row.innerHTML = `
            <td>
                <select
                    name="lote_id[]"
                    class="form-select"
                    required
                >
                    <option value="">
                        Seleccione un lote
                    </option>
                </select>
            </td>

            <td>
                <input
                    type="number"
                    name="cantidad[]"
                    class="form-control"
                    min="0.01"
                    step="0.01"
                    placeholder="0.00"
                    required
                >
            </td>

            <td class="text-end">
                <button
                    type="button"
                    class="btn btn-outline-danger btn-sm remove-dispatch-item"
                    title="Eliminar lote"
                >
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;

        return row;
    };


    addButton.addEventListener("click", () => {
        tableBody.appendChild(createRow());
    });


    tableBody.addEventListener("click", (event) => {
        const removeButton = event.target.closest(".remove-dispatch-item");

        if (!removeButton) {
            return;
        }

        const rows = tableBody.querySelectorAll(".dispatch-item-row");

        if (rows.length <= 1) {
            return;
        }

        removeButton.closest(".dispatch-item-row").remove();
    });
});