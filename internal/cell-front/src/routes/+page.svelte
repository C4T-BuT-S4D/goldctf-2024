<script>
  import SheetList from "./SheetList.svelte";
  import world from "$lib/images/world.png";
  import fileUpload from "$lib/images/file-upload.png";
  import edit from "$lib/images/edit.png";
  import share from "$lib/images/share.png";
  import { get } from "svelte/store";
  import { userData } from "$lib/storage.js";
  import {PUBLIC_BASE_URL} from "$env/static/public";
  import { goto, invalidateAll } from "$app/navigation";

  let error;

  let createModalActive = false;
  let uploadModalActive = false;
  let files;
  let unique = {};

  async function createSheet(event) {
    const data = new FormData(event.currentTarget);
    let title = data.get('title');

    const res = await fetch(`${PUBLIC_BASE_URL}/sheets/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({title: title})
    });
    if (res.ok) {
        await invalidateAll();
        createModalActive = false;
        unique = {};
        return;
    }
    createModalActive = false;
    error = await res.text();
    try {
        error = JSON.parse(error).data.error;
    } catch (err) {
        // ignore
    }
  }

  async function uploadXLSX() {
        if (!files || files.length === 0) {
            return;
        }

        let formData = new FormData();
        formData.append('sheet', files[0]);

        const res = await fetch(`${PUBLIC_BASE_URL}/sheets/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'include',
        });
        if (res.ok) {
            files = null;
            uploadModalActive = false;
            unique = {};
            await invalidateAll();
            return;
        }

        uploadModalActive = false;
        error = await res.text();
        try {
            error = JSON.parse(error).detail.error;
        } catch (e) {
            console.log(e);
        }
    }
</script>

{#if error}
  <p style="color: red">{error}</p>
{/if}
<section class="section">
  <div class="columns is-centered">
    <div class="column is-half has-text-centered">
      <!--            <div class="container is-max-desktop">-->
      {#if $userData.username}
        <h2 class="title is-3">Welcome back, {$userData.username}!</h2>
      {:else}
        <h3 class="title is-3">Welcome to the Cell!</h3>
      {/if}
    </div>
  </div>
</section>
<div class="modal" class:is-active={createModalActive}>
    <div class="modal-background">
    </div>
    <div class="modal-card">
        <header class="modal-card-head">
            <p class="modal-card-title">Create new sheet</p>
            <button class="delete" aria-label="close" on:click={() => createModalActive = false}></button>
        </header>
        <section class="modal-card-body">
            <form on:submit|preventDefault={createSheet}>
                <div class="field">
                    <p class="control">
                        <input class="input" name="title" type="text" placeholder="New sheet">
                    </p>
                </div>
                <div class="field">
                    <p class="control">
                        <input type="submit" value="Create" class="button is-success">
                    </p>
                </div>
            </form>
        </section>
    </div>
</div>
<div class="modal" class:is-active={uploadModalActive}>
    <div class="modal-background">
    </div>
    <div class="modal-card">
        <header class="modal-card-head">
            <p class="modal-card-title">Upload new file</p>
        </header>
        <section class="modal-card-body">
            <div class="file">
                <label class="file-label">
                    <input class="file-input" type="file" name="file" id="file" bind:files>
                    <span class="file-cta">
                      <span class="file-label">
                        Upload XLSX file:
                      </span>
                    </span>
                    <span class="file-name">
                        {#if files && files.length > 0}
                            {files[0].name}
                        {/if}
                    </span>
                </label>
            </div>
        </section>
        <footer class="modal-card-foot">
            <button class="button is-success" on:click={uploadXLSX}>Upload</button>
        </footer>
    </div>
</div>
{#if $userData.username}
  <section class="section">
    <div class="columns is-centered">
      <div class="column is-half has-text-centered">
        {#key unique}
            <SheetList />
        {/key}
      </div>
    </div>
    <div class="columns is-centered">
      <div class="column is-half has-text-centered">
        <button class="button is-info" on:click={() => createModalActive = true}>Create new sheet</button>
      </div>
    </div>
    <div class="columns is-centered">
      <div class="column is-half has-text-centered">
        <button class="button is-info" on:click={() => uploadModalActive = true}>Upload new sheet</button>
      </div>
    </div>
  </section>
{:else}
  <section class="section">
    <nav class="level">
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">Upload excel file</p>
          <p class="title">Upload</p>
          <img alt="" src={fileUpload} width="32px" />
        </div>
      </div>
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">Create the sheet manually</p>
          <p class="title">Create</p>
          <img width="32px" src={edit} alt="" />
        </div>
      </div>
      <div class="level-item has-text-centered">
        <div>
          <p class="heading">Work together.</p>
          <p class="title">Collaborate</p>
          <img width="32px" src={share} alt="" />
        </div>
      </div>
    </nav>
  </section>
  <section class="section">
    <div class="columns is-centered">
      <div class="column is-half has-text-centered">
        <p class="is-size-4">Ready to start?</p>
      </div>
    </div>
    <nav class="level">
      <div class="level-item has-text-centered">
        <div>
          <a class="button is-medium is-link" href="/signin">Sign In</a>
        </div>
      </div>
      <div class="level-item has-text-centered">
        <div>
          <a class="button is-medium is-primary" href="/signup">Sign Up</a>
        </div>
      </div>
    </nav>
  </section>
{/if}
