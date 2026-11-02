import { Routes } from '@angular/router';
import { authGuard } from './core/auth';
export const routes:Routes=[
  {path:'login',loadComponent:()=>import('./pages/login').then(m=>m.LoginPage)},
  {path:'forgot-password',loadComponent:()=>import('./pages/login').then(m=>m.ForgotPage)},
  {path:'reset-password',loadComponent:()=>import('./pages/login').then(m=>m.ResetPage)},
  {path:'unauthorized',loadComponent:()=>import('./pages/login').then(m=>m.UnauthorizedPage)},
  {path:'dashboard',canActivate:[authGuard],loadComponent:()=>import('./pages/dashboard').then(m=>m.DashboardPage)},
  {path:'manage/:resource',canActivate:[authGuard],data:{roles:['admin']},loadComponent:()=>import('./pages/manage').then(m=>m.ManagePage)},
  {path:'attendance',canActivate:[authGuard],loadComponent:()=>import('./pages/attendance').then(m=>m.AttendancePage)},
  {path:'marks',canActivate:[authGuard],data:{roles:['admin','teacher']},loadComponent:()=>import('./pages/marks').then(m=>m.MarksPage)},
  {path:'results',canActivate:[authGuard],loadComponent:()=>import('./pages/results').then(m=>m.ResultsPage)},
  {path:'reports',canActivate:[authGuard],data:{roles:['admin','teacher']},loadComponent:()=>import('./pages/reports').then(m=>m.ReportsPage)},
  {path:'settings',canActivate:[authGuard],data:{roles:['admin']},loadComponent:()=>import('./pages/settings').then(m=>m.SettingsPage)},
  {path:'',pathMatch:'full',redirectTo:'dashboard'},
  {path:'**',redirectTo:'dashboard'}
];
