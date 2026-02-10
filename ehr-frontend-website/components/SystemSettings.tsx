import React, { useState, useEffect } from 'react';
import { Save, Camera, User as UserIcon, Mail, Building, Briefcase, AtSign } from 'lucide-react';
import { User } from '../types';
import { authService } from '../services/authService';

interface SystemSettingsProps {
    currentUser: User;
    onUpdateUser: (user: User) => void;
}

const SystemSettings: React.FC<SystemSettingsProps> = ({ currentUser, onUpdateUser }) => {
    const [formData, setFormData] = useState<User>(currentUser);
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

    // Sync if currentUser prop changes externally
    useEffect(() => {
        setFormData(currentUser);
    }, [currentUser]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            const reader = new FileReader();
            reader.onloadend = () => {
                setFormData(prev => ({ ...prev, profileImage: reader.result as string }));
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage(null);

        try {
            const updatedUser = await authService.updateProfile(formData);
            onUpdateUser(updatedUser);
            setMessage({ type: 'success', text: 'Profile updated successfully.' });
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to update profile.' });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto">
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-slate-800">System Settings</h2>
                <p className="text-slate-500">Manage your personal information and account preferences.</p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <form onSubmit={handleSubmit}>
                    {/* Header Image Section */}
                    <div className="p-8 border-b border-slate-100 flex flex-col sm:flex-row items-center gap-8">
                        <div className="relative group">
                            <div className="w-24 h-24 rounded-full bg-slate-100 border-4 border-white shadow-lg flex items-center justify-center overflow-hidden">
                                {formData.profileImage ? (
                                    <img src={formData.profileImage} alt="Profile" className="w-full h-full object-cover" />
                                ) : (
                                    <span className="text-3xl font-bold text-slate-400">
                                        {formData.name.charAt(0)}
                                    </span>
                                )}
                            </div>
                            <label className="absolute bottom-0 right-0 p-1.5 bg-brand-600 text-white rounded-full cursor-pointer shadow-md hover:bg-brand-700 transition-colors">
                                <Camera size={16} />
                                <input type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
                            </label>
                        </div>
                        <div className="text-center sm:text-left">
                            <h3 className="text-lg font-semibold text-slate-900">{formData.name}</h3>
                            <p className="text-sm text-slate-500">{formData.role}</p>
                            <p className="text-xs text-slate-400 mt-1 font-mono">{formData.organization}</p>
                        </div>
                    </div>

                    {/* Form Fields */}
                    <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                        {message && (
                            <div className={`col-span-1 md:col-span-2 p-4 rounded-lg text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                                {message.text}
                            </div>
                        )}

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-slate-700">Full Name</label>
                            <div className="relative">
                                <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                                <input 
                                    name="name"
                                    type="text"
                                    value={formData.name}
                                    onChange={handleChange}
                                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-slate-700">Username</label>
                            <div className="relative">
                                <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                                <input 
                                    name="username"
                                    type="text"
                                    readOnly // Usually usernames are immutable
                                    value={formData.username}
                                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed outline-none"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-slate-700">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                                <input 
                                    name="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-slate-700">Secondary Email</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                                <input 
                                    name="secondaryEmail"
                                    type="email"
                                    value={formData.secondaryEmail || ''}
                                    onChange={handleChange}
                                    placeholder="Optional"
                                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-slate-700">Organization</label>
                            <div className="relative">
                                <Building className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                                <input 
                                    name="organization"
                                    type="text"
                                    value={formData.organization}
                                    onChange={handleChange}
                                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-slate-700">Position / Title</label>
                            <div className="relative">
                                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
                                <input 
                                    name="position"
                                    type="text"
                                    value={formData.position || ''}
                                    onChange={handleChange}
                                    placeholder="e.g. Chief Resident"
                                    className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-slate-700">Pronouns</label>
                            <select 
                                name="pronoun" 
                                value={formData.pronoun || ''} 
                                onChange={handleChange}
                                className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 outline-none bg-white"
                            >
                                <option value="">Select pronouns</option>
                                <option value="He/Him">He/Him</option>
                                <option value="She/Her">She/Her</option>
                                <option value="They/Them">They/Them</option>
                                <option value="Prefer not to say">Prefer not to say</option>
                            </select>
                        </div>
                    </div>

                    <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-end">
                        <button 
                            type="submit"
                            disabled={isLoading}
                            className="flex items-center gap-2 px-6 py-2 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-colors disabled:opacity-70"
                        >
                            <Save size={18} />
                            {isLoading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default SystemSettings;
