$old = "      <a href=`"#`">Membership</a>`n    </nav>`n  </div>`n</header>"

$new = @'
      <a href="#">Membership</a>
      <span id="authStatus"></span>
    </nav>
  </div>
</header>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(function () {
  const _sbAuth = window.supabase.createClient("https://zvzccgbzfmnjzjyqxaay.supabase.co", "sb_publishable_Rfp5FzznTrV9UFldAQCvrg_2bu6oVDT");
  const el = document.getElementById('authStatus');
  if (el) {
    _sbAuth.auth.getSession().then(function (res) {
      const session = res.data.session;
      if (session) {
        el.innerHTML = '<a href="#" id="logoutLink">Log Out</a>';
        document.getElementById('logoutLink').onclick = function (e) {
          e.preventDefault();
          _sbAuth.auth.signOut().then(function () { window.location.reload(); });
        };
      } else {
        el.innerHTML = '<a href="#" id="loginLink">Log In</a>';
        document.getElementById('loginLink').onclick = function (e) {
          e.preventDefault();
          const email = prompt('Enter your email to receive a login link:');
          if (!email) return;
          _sbAuth.auth.signInWithOtp({ email: email }).then(function (r) {
            alert(r.error ? ('Something went wrong: ' + r.error.message) : 'Check your email for a login link.');
          });
        };
      }
    });
  }
})();
</script>
'@

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$files = Get-ChildItem -Filter *.html
$updated = 0
foreach ($file in $files) {
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)
    if ($content.Contains($old)) {
        $content = $content.Replace($old, $new)
        [System.IO.File]::WriteAllText($file.FullName, $content, $utf8NoBom)
        $updated++
    }
}
Write-Host "Updated $updated of $($files.Count) files"