<script>
    import {PUBLIC_BASE_URL} from "$env/static/public";
    import {invalidateAll} from "$app/navigation";
    import { Centrifuge } from 'centrifuge';
    import { onMount } from 'svelte';
    import { Sheet } from "svelte-sheets";

    /** @type {import('./$types').PageData} */
    export let data;

    const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    let sheet = data.sheet.data;
    let tokens = data.sheet.tokens;
    let error = data.error;
    let canEdit = tokens?.write != null;
    let viewerLink = `/sheet/${data.sheet.id}?readToken=${tokens?.read}`;
    let editorLink = canEdit ? `/sheet/${data.sheet.id}?readToken=${tokens?.read}&writeToken=${tokens?.write}` : null;


    $: cellsData = parseSheetData(sheet.cells);
    $: headers = cellsData[0];
    $: mainData = cellsData.slice(1);

    let host = PUBLIC_BASE_URL.startsWith("/") ? window.location.host: PUBLIC_BASE_URL.slice(0, "/api".length * -1).slice("http://".length);
    const centrifuge = new Centrifuge("ws://" + host + "/connection/websocket");
    const sub = centrifuge.newSubscription(`sheets:${data.sheet.id}`, {
        data: {
            authToken: tokens?.read
        }
    });

    sub.on("publication", handleSheetUpdates);


    async function handleSheetUpdates(ctx) {
        if (ctx.channel !== `sheets:${data.sheet.id}`) {
            return;
        }
        let updated_cells = ctx.data.cells;
        cellsData = parseSheetData(updated_cells);
    }

    async function saveCellUpdate(row, col, value) {
        console.log(canEdit, tokens);
        if (!canEdit) {
            return;
        }

        let excelCol = toExcelColumn(col);
        let addr = `${excelCol}${row+1}`;
        
        await centrifuge.rpc("sheets.write", {
            sheetId: data.sheet.id,
            cell: addr,
            value: value,
            authToken: tokens?.write
        }).then((res) => {
            if (res.data.error) {
                error = res.data.error;
            }
        }).catch((err) => {
            error = err;
        });
    }


    function toExcelColumn(ind) {
        let col = "";
        while (ind > 0) {
            let remainder = (ind - 1) % 26
            col = ALPHABET[remainder] + col;
            ind = Math.floor((ind - 1) / 26);
        }
        return col;
    }

    function parseSheetData(cells) {
        let matrix = [];
        const width = 10;
        const height = 20;
        for(var i=0; i<height; i++) {
            matrix[i] = new Array(width).fill("");
        }

        for (let cell of cells) {
            let row = cell.row;
            let col = cell.col;
            let colInt = 0;

            for (let c in col) {
                colInt = colInt * 26 + ALPHABET.indexOf(col[c]) + 1;
            }
            let value = cell.val ?? "";
            matrix[row][colInt] = value;
        }

        for (let j = 1; j < width; j++) {
            matrix[0][j] = toExcelColumn(j);
        }
        for (let i = 0; i < height; i++) {
            matrix[i][0] = i;
        }

        return matrix;
    }

    onMount(async () => {
        if (error) {
            return;
        }
        sub.subscribe();
        centrifuge.connect();
    });
</script>

{#if error}
    <div class="notification is-danger">
        {error}
    </div>
{/if}

<div class="columns">
    <div class="column is-half has-text-centered">
        <h4 class="subtitle is-4">{sheet.title}</h4>
    </div>
    
    <div class="column"><a href="{viewerLink}">Viewer link</a></div>
    {#if canEdit}
        <div class="column"><a href="{editorLink}">Editor link</a></div>
    {/if}
  </div>

<table class="table is-fullwidth is-bordered">
    <thead>
      <tr>
        {#each headers as h}
          <th class="has-text-centered">{h}</th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each mainData as row, rowIdx}
        <tr>
          {#each row as col, colIdx}
          {#if colIdx == 0 || !canEdit}
            <td class="has-text-centered">{col}</td>
            {:else}
            <!-- <td class="has-text-centered">{col}</td> -->
            <td class="has-text-centered">
                <input class="input" type="text" bind:value={mainData[rowIdx][colIdx]} on:change={() => saveCellUpdate(rowIdx, colIdx, mainData[rowIdx][colIdx])} />
            </td>
            {/if}
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
  
  <style>
    table {
      border-collapse: collapse;
    }
  
    th,
    td {
      border: 1px solid #ddd;
      padding: 8px;
    }
  </style>

