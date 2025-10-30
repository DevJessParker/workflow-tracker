// Sample TypeScript/Angular code to demonstrate workflow detection capabilities

import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, filter, switchMap, catchError } from 'rxjs/operators';

/**
 * Sample Angular service demonstrating various data workflow patterns
 * that Workflow Tracker can detect and document.
 */
@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly apiUrl = 'https://api.example.com';

  constructor(private http: HttpClient) {}

  // API CALL - Will be detected as HTTP GET operation
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.apiUrl}/users`);
  }

  // API CALL - Will be detected as HTTP GET with parameter
  getUserById(id: number): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/users/${id}`);
  }

  // API CALL - Will be detected as HTTP POST operation
  createUser(user: User): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/users`, user);
  }

  // API CALL - Will be detected as HTTP PUT operation
  updateUser(id: number, user: User): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/users/${id}`, user);
  }

  // API CALL - Will be detected as HTTP DELETE operation
  deleteUser(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/users/${id}`);
  }

  // DATA TRANSFORM - Will be detected as RxJS transformation pipeline
  getUsersWithProfiles(): Observable<UserWithProfile[]> {
    return this.http.get<User[]>(`${this.apiUrl}/users`)
      .pipe(
        map(users => users.filter(u => u.active)),
        switchMap(users => this.enrichWithProfiles(users)),
        map(users => this.transformToViewModel(users))
      );
  }

  // WORKFLOW: API -> Transform -> Cache
  // This will show as a connected workflow
  loadAndCacheUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.apiUrl}/users`)
      .pipe(
        map(users => {
          // Data transformation
          return users.map(u => ({
            ...u,
            displayName: `${u.firstName} ${u.lastName}`
          }));
        }),
        map(users => {
          // Cache write - will be detected
          localStorage.setItem('users', JSON.stringify(users));
          return users;
        })
      );
  }

  // CACHE READ - Will be detected as localStorage read
  getCachedUsers(): User[] | null {
    const cached = localStorage.getItem('users');
    return cached ? JSON.parse(cached) : null;
  }

  // CACHE WRITE - Will be detected as localStorage write
  cacheUserPreferences(userId: number, preferences: UserPreferences): void {
    localStorage.setItem(`user_${userId}_prefs`, JSON.stringify(preferences));
  }

  // SESSION STORAGE - Will be detected as sessionStorage operations
  saveSessionData(key: string, data: any): void {
    sessionStorage.setItem(key, JSON.stringify(data));
  }

  getSessionData(key: string): any {
    const data = sessionStorage.getItem(key);
    return data ? JSON.parse(data) : null;
  }

  // COMPLEX WORKFLOW: Multiple API calls with transformations
  getUserDashboardData(userId: number): Observable<DashboardData> {
    // API call 1: Get user
    return this.http.get<User>(`${this.apiUrl}/users/${userId}`)
      .pipe(
        // API call 2: Get user's orders
        switchMap(user =>
          this.http.get<Order[]>(`${this.apiUrl}/users/${userId}/orders`)
            .pipe(map(orders => ({ user, orders })))
        ),
        // API call 3: Get user's activity
        switchMap(({ user, orders }) =>
          this.http.get<Activity[]>(`${this.apiUrl}/users/${userId}/activity`)
            .pipe(map(activity => ({ user, orders, activity })))
        ),
        // Data transformation
        map(({ user, orders, activity }) => {
          return {
            userName: user.firstName + ' ' + user.lastName,
            totalOrders: orders.length,
            recentActivity: activity.slice(0, 10),
            lastLoginDate: new Date(user.lastLogin)
          };
        }),
        // Cache the result
        map(dashboard => {
          localStorage.setItem('dashboard', JSON.stringify(dashboard));
          return dashboard;
        })
      );
  }

  // FILE OPERATIONS - Will be detected if browser File API is used
  exportUsersToFile(users: User[]): void {
    const data = JSON.stringify(users, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'users.json';
    link.click();

    window.URL.revokeObjectURL(url);
  }

  // FILE READ - Will be detected as FileReader operation
  importUsersFromFile(file: File): Observable<User[]> {
    return new Observable(observer => {
      const reader = new FileReader();

      reader.onload = (e) => {
        const content = e.target?.result as string;
        const users = JSON.parse(content);
        observer.next(users);
        observer.complete();
      };

      reader.readAsText(file);
    });
  }

  // WORKFLOW: Fetch from multiple APIs and combine
  getUserWithRelatedData(userId: number): Observable<UserDetailView> {
    const user$ = this.http.get<User>(`${this.apiUrl}/users/${userId}`);
    const posts$ = this.http.get<Post[]>(`${this.apiUrl}/users/${userId}/posts`);
    const comments$ = this.http.get<Comment[]>(`${this.apiUrl}/users/${userId}/comments`);

    return user$.pipe(
      switchMap(user =>
        posts$.pipe(
          switchMap(posts =>
            comments$.pipe(
              map(comments => ({
                ...user,
                posts,
                comments,
                totalContent: posts.length + comments.length
              }))
            )
          )
        )
      )
    );
  }

  private enrichWithProfiles(users: User[]): Observable<UserWithProfile[]> {
    // Another API call in the pipeline
    return this.http.post<UserWithProfile[]>(`${this.apiUrl}/users/enrich`, {
      userIds: users.map(u => u.id)
    });
  }

  private transformToViewModel(users: any[]): UserWithProfile[] {
    // Data transformation logic
    return users.map(u => ({
      id: u.id,
      name: `${u.firstName} ${u.lastName}`,
      email: u.email,
      profileUrl: u.profile?.avatarUrl || '/default-avatar.png'
    }));
  }
}

// Supporting interfaces
interface User {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  active: boolean;
  lastLogin: string;
}

interface UserWithProfile extends User {
  profileUrl: string;
  name: string;
}

interface UserPreferences {
  theme: string;
  notifications: boolean;
}

interface Order {
  id: number;
  date: string;
  total: number;
}

interface Activity {
  id: number;
  type: string;
  timestamp: string;
}

interface DashboardData {
  userName: string;
  totalOrders: number;
  recentActivity: Activity[];
  lastLoginDate: Date;
}

interface Post {
  id: number;
  title: string;
  content: string;
}

interface Comment {
  id: number;
  postId: number;
  content: string;
}

interface UserDetailView extends User {
  posts: Post[];
  comments: Comment[];
  totalContent: number;
}
