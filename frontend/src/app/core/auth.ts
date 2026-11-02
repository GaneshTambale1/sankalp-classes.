import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { CanActivateFn, Router } from '@angular/router';
import { tap, catchError, throwError } from 'rxjs';
import { environment } from '../../environments/environment';

export interface User {id: number; email: string; full_name: string; role: 'admin'|'teacher'|'student'; active: boolean}
interface LoginResponse {access_token: string; user: User}
@Injectable({providedIn: 'root'})
export class AuthService {
  private http=inject(HttpClient);
  private storageKey='sankalp_session';
  private initialUser():User|null {try {return JSON.parse(sessionStorage.getItem(this.storageKey+'_user') || 'null') as User|null;}catch{return null;}}
  user=signal<User|null>(this.initialUser());
  role=computed(()=>this.user()?.role || '');
  token(): string {return sessionStorage.getItem(this.storageKey) || '';}
  login(email:string,password:string) {return this.http.post<LoginResponse>(`${environment.apiUrl}/auth/login`,{email,password}).pipe(tap(r=>{
    sessionStorage.setItem(this.storageKey,r.access_token);sessionStorage.setItem(this.storageKey+'_user',JSON.stringify(r.user));this.user.set(r.user);
  }));}
  clear():void {sessionStorage.removeItem(this.storageKey);sessionStorage.removeItem(this.storageKey+'_user');this.user.set(null);}
  logout() {const request=this.http.post(`${environment.apiUrl}/auth/logout`,{});request.subscribe({next:()=>this.clear(),error:()=>this.clear()});}
  refresh() {return this.http.get<{user:User}>(`${environment.apiUrl}/auth/me`).pipe(tap(r=>{this.user.set(r.user);sessionStorage.setItem(this.storageKey+'_user',JSON.stringify(r.user));}));}
}
export const tokenInterceptor: HttpInterceptorFn=(req,next)=>{
  const auth=inject(AuthService);
  const token=auth.token();
  const modified=token && req.url.startsWith(environment.apiUrl) ? req.clone({setHeaders:{Authorization:`Bearer ${token}`}}):req;
  return next(modified).pipe(catchError((err:HttpErrorResponse)=>{
    if (err.status===401 && !req.url.endsWith('/auth/login'))auth.clear();
    return throwError(()=>err);
  }));
};
export const authGuard: CanActivateFn=(route)=>{
  const auth=inject(AuthService),router=inject(Router);
  if (!auth.token())return router.parseUrl('/login');
  const allowed=route.data['roles'] as string[]|undefined;
  return allowed && !allowed.includes(auth.role())?router.parseUrl('/unauthorized'):true;
};
