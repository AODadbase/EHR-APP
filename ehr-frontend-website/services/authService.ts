import { User } from '../types';

const USERS_KEY = 'traceable_health_users';
const SESSION_KEY = 'traceable_health_session';

export const authService = {
  login: async (username: string, password: string): Promise<User> => {
    // Simulated API latency
    await new Promise(resolve => setTimeout(resolve, 800));

    const usersStr = localStorage.getItem(USERS_KEY);
    const users = usersStr ? JSON.parse(usersStr) : [];
    
    const user = users.find((u: any) => u.username === username && u.password === password);
    
    if (user) {
      // Normalize user object and apply defaults
      const userData: User = { 
        username: user.username, 
        name: user.name, 
        role: user.role || 'Medical Staff',
        email: user.email || '',
        organization: user.organization || '',
        position: user.position || '',
        pronoun: user.pronoun || '',
        secondaryEmail: user.secondaryEmail || '',
        profileImage: user.profileImage || undefined
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
      return userData;
    }
    
    throw new Error('Invalid credentials');
  },

  sendVerificationCode: async (email: string): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1500));
    // In production, this would call a backend email service.
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    console.log(`[MOCK EMAIL SERVICE] Sent verification code ${code} to ${email}`);
    alert(`[DEMO] Your verification code is: ${code}`); 
    return code;
  },

  register: async (data: any): Promise<User> => {
    await new Promise(resolve => setTimeout(resolve, 800));

    const usersStr = localStorage.getItem(USERS_KEY);
    const users = usersStr ? JSON.parse(usersStr) : [];
    
    if (users.find((u: any) => u.username === data.username)) {
      throw new Error('Username already exists');
    }

    const newUser = { 
        ...data,
        role: data.position || 'Resident Physician' 
    };
    
    users.push(newUser);
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
    
    // Store session object without password
    const { password, ...userData } = newUser;
    localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
    
    return userData as User;
  },

  updateProfile: async (user: User): Promise<User> => {
    await new Promise(resolve => setTimeout(resolve, 600));

    const usersStr = localStorage.getItem(USERS_KEY);
    let users = usersStr ? JSON.parse(usersStr) : [];

    // Update stored profile data
    users = users.map((u: any) => {
        if (u.username === user.username) {
            return { ...u, ...user }; // Merge updates
        }
        return u;
    });

    localStorage.setItem(USERS_KEY, JSON.stringify(users));
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));

    return user;
  },

  logout: () => {
    localStorage.removeItem(SESSION_KEY);
  },

  getCurrentUser: (): User | null => {
    const sessionStr = localStorage.getItem(SESSION_KEY);
    if (sessionStr) {
      return JSON.parse(sessionStr);
    }
    return null;
  }
};