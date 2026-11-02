import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { AuthService } from '../core/auth';
import { ApiService, readableError } from '../core/api';
@Component({standalone:true,imports:[CommonModule,ReactiveFormsModule,RouterLink],template:`
<div class="auth-background"><div class="login-layout"><div class="login-intro"><div class="brand brand-white"><div class="brand-mark">S</div><div><strong>SANKALP</strong><small>CLASSES</small></div></div><div class="auth-message"><div class="pill-white">THE SMARTER WAY TO MANAGE LEARNING</div><h1>Every student.<br>Every milestone.<br><span>One place.</span></h1><p>Manage your institute with clarity. Attendance, examinations, results and progress—all seamlessly connected.</p></div><div class="auth-footer">© 2026 Sankalp Classes</div></div><div class="auth-form-pane"><div class="login-card"><div class="login-symbol"><i class="bi bi-mortarboard"></i></div><h2>Welcome back</h2><p class="muted">Sign in to continue to your workspace.</p>
@if(message()){<div class="alert alert-danger">{{message()}}</div>}
<form [formGroup]="form" (ngSubmit)="login()"><label class="form-label" for="email">Email address</label><input id="email" class="form-control mb-3" formControlName="email" type="email" placeholder="you@example.com" autocomplete="username"><label class="form-label" for="password">Password</label><input id="password" class="form-control mb-2" formControlName="password" type="password" placeholder="Enter your password" autocomplete="current-password"><div class="text-end mb-4"><a routerLink="/forgot-password" class="subtle-link">Forgot password?</a></div><button class="btn btn-primary w-100" type="submit" [disabled]="form.invalid||busy()">{{busy()?'Signing in…':'Sign in'}} <i class="bi bi-arrow-right"></i></button></form><div class="small muted mt-4">Access is limited to accounts created by your institute administrator.</div></div></div></div></div>
`})
export class LoginPage {
 private fb=inject(FormBuilder);private auth=inject(AuthService);private router=inject(Router);
 form=this.fb.nonNullable.group({email:['',[Validators.required,Validators.email]],password:['',Validators.required]});
 message=signal('');busy=signal(false);
 login(){if(this.form.invalid)return;this.busy.set(true);this.message.set('');this.auth.login(this.form.value.email!,this.form.value.password!).subscribe({next:()=>this.router.navigateByUrl('/dashboard'),error:e=>{this.busy.set(false);this.message.set(readableError(e));}});}
}
@Component({standalone:true,imports:[ReactiveFormsModule,RouterLink],template:`<div class="simple-auth"><div class="login-card"><h2>Reset your password</h2><p class="muted">Enter your account email. Instructions will be sent if email delivery is configured.</p><form [formGroup]="form" (ngSubmit)="submit()"><input class="form-control mb-3" type="email" formControlName="email" placeholder="Email address"><button class="btn btn-primary" [disabled]="form.invalid">Send reset link</button></form><p class="mt-3">{{message()}}</p><a routerLink="/login">Back to login</a></div></div>`})
export class ForgotPage {
 private fb=inject(FormBuilder);private api=inject(ApiService);
 form=this.fb.nonNullable.group({email:['',[Validators.required,Validators.email]]});message=signal('');
 submit(){this.api.post<{message:string}>('auth/forgot-password',this.form.value).subscribe({next:r=>this.message.set(r.message),error:e=>this.message.set(readableError(e))});}
}
@Component({standalone:true,imports:[ReactiveFormsModule,RouterLink],template:`<div class="simple-auth"><div class="login-card"><h2>Choose a new password</h2><p class="muted">Use a password with at least 12 characters.</p><form [formGroup]="form" (ngSubmit)="submit()"><input class="form-control mb-3" type="password" formControlName="password" placeholder="New password"><button class="btn btn-primary" [disabled]="form.invalid">Update password</button></form><p class="mt-3">{{message()}}</p><a routerLink="/login">Return to login</a></div></div>`})
export class ResetPage {
 private fb=inject(FormBuilder);private api=inject(ApiService);private route=inject(ActivatedRoute);
 form=this.fb.nonNullable.group({password:['',[Validators.required,Validators.minLength(12)]]});message=signal('');
 submit(){this.api.post<{message:string}>('auth/reset-password',{token:this.route.snapshot.queryParamMap.get('token'),password:this.form.value.password}).subscribe({next:r=>this.message.set(r.message),error:e=>this.message.set(readableError(e))});}
}
@Component({standalone:true,imports:[RouterLink],template:`<div class="simple-auth"><div class="login-card"><h2>Access restricted</h2><p>You do not have permission to view this page.</p><a routerLink="/dashboard" class="btn btn-primary">Back to dashboard</a></div></div>`})
export class UnauthorizedPage {}
