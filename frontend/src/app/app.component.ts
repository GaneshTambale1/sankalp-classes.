import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './core/auth';
interface NavItem {title:string;route:string;icon:string;roles:string[]}
@Component({selector:'app-root',standalone:true,imports:[CommonModule,RouterOutlet,RouterLink,RouterLinkActive],template:`
@if(auth.user()) {
<div class="app-shell">
 <aside class="sidebar" [class.open]="menuOpen()">
  <div class="brand"><div class="brand-mark">S</div><div><strong>SANKALP</strong><small>CLASSES</small></div></div>
  <div class="nav-label">WORKSPACE</div>
  <nav class="side-nav">
   @for(item of available(); track item.route) {
    <a [routerLink]="item.route" routerLinkActive="active" (click)="menuOpen.set(false)"><i class="bi {{item.icon}}"></i><span>{{item.title}}</span></a>
   }
  </nav>
  <div class="side-bottom"><small>Institute Management</small><strong>Academic excellence, simplified.</strong></div>
 </aside>
 <div class="main-column">
  <header class="topbar"><button class="icon-button mobile-menu" aria-label="Menu" (click)="menuOpen.set(!menuOpen())"><i class="bi bi-list"></i></button>
    <div class="header-title">Sankalp Classes <span class="muted">/ Management Portal</span></div>
    <div class="account"><div class="avatar">{{auth.user()?.full_name?.charAt(0)?.toUpperCase()}}</div><div class="account-info"><strong>{{auth.user()?.full_name}}</strong><small>{{auth.user()?.role | titlecase}}</small></div><button class="icon-button" title="Sign out" (click)="signOut()"><i class="bi bi-box-arrow-right"></i></button></div>
  </header>
  <main class="content"><router-outlet /></main>
 </div>
</div>
@if(menuOpen()){<button class="mobile-overlay" aria-label="Close menu" (click)="menuOpen.set(false)"></button>}
} @else {<router-outlet />}
`})
export class AppComponent {
  auth=inject(AuthService); router=inject(Router);menuOpen=signal(false);
  nav:NavItem[]=[
    {title:'Dashboard',route:'/dashboard',icon:'bi-grid-1x2',roles:['admin','teacher','student']},
    {title:'Students',route:'/manage/students',icon:'bi-people',roles:['admin']},
    {title:'Teachers',route:'/manage/teachers',icon:'bi-person-workspace',roles:['admin']},
    {title:'Classes',route:'/manage/classes',icon:'bi-building',roles:['admin']},
    {title:'Batches',route:'/manage/batches',icon:'bi-collection',roles:['admin']},
    {title:'Subjects',route:'/manage/subjects',icon:'bi-book',roles:['admin']},
    {title:'Class Subjects',route:'/manage/class-subjects',icon:'bi-journal-check',roles:['admin']},
    {title:'Teacher Assignments',route:'/manage/teacher-assignments',icon:'bi-person-check',roles:['admin']},
    {title:'Attendance',route:'/attendance',icon:'bi-calendar-check',roles:['admin','teacher','student']},
    {title:'Examinations',route:'/manage/examinations',icon:'bi-file-earmark-text',roles:['admin']},
    {title:'Exam Subjects',route:'/manage/examination-subjects',icon:'bi-ui-checks',roles:['admin']},
    {title:'Marks Entry',route:'/marks',icon:'bi-pencil-square',roles:['admin','teacher']},
    {title:'Results',route:'/results',icon:'bi-trophy',roles:['admin','teacher','student']},
    {title:'Reports',route:'/reports',icon:'bi-bar-chart',roles:['admin','teacher']},
    {title:'Settings',route:'/settings',icon:'bi-gear',roles:['admin']}
  ];
  available(){return this.nav.filter(n=>n.roles.includes(this.auth.role()));}
  signOut(){this.auth.logout();this.router.navigateByUrl('/login');}
}
