<script>
    import 'bulma/css/bulma.css';
    import gold from '$lib/images/gold.png';

    import { userData } from '$lib/storage.js';
</script>


<nav class="navbar is-link" role="navigation" aria-label="main navigation">
    <div class="navbar-brand">
        <a class="navbar-item" href="/">
            <img src={gold} alt="" />
            <p>Cell</p>
        </a>
    </div>

    <div class="navbar-end">
        <div class="navbar-item">
            <div class="buttons">
        {#if $userData.uid}
            <a class="button is-primary" href="/logout" role="button">
                Logout
            </a>
        {:else}
            <a class="button is-light" href="/signin" role="button">
                Sign in
            </a>
            <a class="button is-primary" href="/signup" role="button">
                <strong>
                    Sign Up
                </strong>
            </a>
        {/if}
            </div>
        </div>
    </div>
</nav>

<main>

    <slot></slot>
</main>
